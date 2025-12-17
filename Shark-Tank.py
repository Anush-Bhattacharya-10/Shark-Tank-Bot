import discord
from discord import app_commands
from discord.ext import commands
import uuid
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ========== CONFIG ==========
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Role IDs - Set by admin via commands
SHARK_ROLE_ID = None
ENTREPRENEUR_ROLE_ID = None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== GAME CONFIG (Modifiable by Admins) ==========
game_config = {
    "shark_starting_money": 1000000,
    "season_active": False,
    "season_start": None,
    "investment_deadline_hours": 48
}

# Investment pricing tiers
INVESTMENT_TIERS = {
    "1": {"cost": 25000, "quality_boost": 1, "name": "Basic Growth"},
    "2": {"cost": 75000, "quality_boost": 3, "name": "Moderate Expansion"},
    "3": {"cost": 150000, "quality_boost": 5, "name": "Aggressive Scale"}
}

# ========== GLOBAL STATE ==========
player_money = {}  # Track everyone's money: {user_id: amount}
player_investments = {}  # Track entrepreneur investments: {user_id: {business_id: capital}}
businesses = {}  # Track all businesses: {business_id: {...}}
eliminated_entrepreneurs = set()  # Entrepreneurs who walked away or failed to get deals

round_data = {
    "active": False,
    "entrepreneur_id": None,
    "entrepreneur_name": None,
    "pitch": None,
    "asking_amount": None,
    "asking_equity": None,
    "business_id": None,
    "business_quality": None,  # Hidden score 1-10
    "offers": {},
    "negotiations": []
}

leaderboard = {
    "entrepreneurs": {},
    "sharks": {}
}


# ========== HELPERS ==========
def new_offer_id():
    return str(uuid.uuid4())[:8]


def new_business_id():
    return str(uuid.uuid4())[:8]


def ensure_user(store, uid, name):
    if uid not in store:
        store[uid] = {
            "name": name,
            "pitches": 0,
            "deals": 0,
            "rejected": 0,
            "invested": 0
        }


def ensure_player_money(uid, is_shark=True):
    """Initialize player money if not exists"""
    if uid not in player_money:
        if is_shark:
            player_money[uid] = game_config["shark_starting_money"]
        else:
            player_money[uid] = 0  # Entrepreneurs start with $0


def has_role(member, role_id):
    if role_id is None:
        return False
    return any(role.id == role_id for role in member.roles)


def add_negotiation_log(actor, action, details):
    """Log negotiation steps"""
    round_data["negotiations"].append({
        "actor": actor,
        "action": action,
        "details": details
    })


def calculate_business_outcome(business_id):
    """Calculate if business succeeds and final valuations"""
    business = businesses[business_id]
    quality_score = business["final_quality"]
    initial_valuation = business["valuation"]

    # Quality score affects success chance (10% per point, max 100%)
    success_chance = min(quality_score * 10, 100)

    if random.randint(1, 100) <= success_chance:
        # Success! Valuation grows by 1.5x to 5x based on quality
        multiplier = 1.5 + (quality_score / 10 * 3.5)
        final_valuation = initial_valuation * multiplier
        return True, final_valuation, multiplier
    else:
        # Failure - business worth 0
        return False, 0, 0


# ========== ADMIN COMMANDS ==========
@bot.tree.command(name="admin_set_roles", description="[ADMIN] Set the Shark and Entrepreneur role IDs")
@app_commands.describe(
    shark_role="The role for Sharks",
    entrepreneur_role="The role for Entrepreneurs"
)
@app_commands.checks.has_permissions(administrator=True)
async def admin_set_roles(interaction: discord.Interaction, shark_role: discord.Role, entrepreneur_role: discord.Role):
    """Set game roles"""
    global SHARK_ROLE_ID, ENTREPRENEUR_ROLE_ID

    SHARK_ROLE_ID = shark_role.id
    ENTREPRENEUR_ROLE_ID = entrepreneur_role.id

    embed = discord.Embed(title="✅ Roles Configured", color=discord.Color.green())
    embed.add_field(name="🦈 Shark Role", value=shark_role.mention, inline=False)
    embed.add_field(name="👔 Entrepreneur Role", value=entrepreneur_role.mention, inline=False)
    embed.set_footer(text="Players with these roles can now participate!")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="admin_config", description="[ADMIN] View current game configuration")
@app_commands.checks.has_permissions(administrator=True)
async def admin_config(interaction: discord.Interaction):
    """View game config"""
    embed = discord.Embed(title="⚙️ Game Configuration", color=discord.Color.blue())

    # Role info
    shark_role = interaction.guild.get_role(SHARK_ROLE_ID) if SHARK_ROLE_ID else None
    entrepreneur_role = interaction.guild.get_role(ENTREPRENEUR_ROLE_ID) if ENTREPRENEUR_ROLE_ID else None

    embed.add_field(
        name="🦈 Shark Role",
        value=shark_role.mention if shark_role else "❌ Not set",
        inline=False
    )
    embed.add_field(
        name="👔 Entrepreneur Role",
        value=entrepreneur_role.mention if entrepreneur_role else "❌ Not set",
        inline=False
    )

    embed.add_field(name="Shark Starting Money", value=f"${game_config['shark_starting_money']:,}")
    embed.add_field(name="Investment Deadline", value=f"{game_config['investment_deadline_hours']} hours")
    embed.add_field(name="Season Active", value="✅ Yes" if game_config['season_active'] else "❌ No")
    embed.add_field(name="Active Businesses", value=str(len(businesses)))
    embed.add_field(name="Eliminated Entrepreneurs", value=str(len(eliminated_entrepreneurs)))

    if not shark_role or not entrepreneur_role:
        embed.add_field(
            name="⚠️ Setup Required",
            value="Use `/admin_set_roles` to configure roles before starting!",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="admin_set_shark_money", description="[ADMIN] Set starting money for sharks")
@app_commands.describe(amount="Starting money for sharks")
@app_commands.checks.has_permissions(administrator=True)
async def admin_set_shark_money(interaction: discord.Interaction, amount: int):
    """Set shark starting money"""
    game_config["shark_starting_money"] = amount
    await interaction.response.send_message(f"✅ Shark starting money set to ${amount:,}")


@bot.tree.command(name="admin_set_deadline", description="[ADMIN] Set investment deadline in hours")
@app_commands.describe(hours="Hours after deal closes for entrepreneurs to invest")
@app_commands.checks.has_permissions(administrator=True)
async def admin_set_deadline(interaction: discord.Interaction, hours: int):
    """Set investment deadline"""
    game_config["investment_deadline_hours"] = hours
    await interaction.response.send_message(f"✅ Investment deadline set to {hours} hours")


@bot.tree.command(name="admin_give_money", description="[ADMIN] Give money to a player")
@app_commands.describe(
    user="The user to give money to",
    amount="Amount of money to give"
)
@app_commands.checks.has_permissions(administrator=True)
async def admin_give_money(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Give money to player"""
    if user.id not in player_money:
        player_money[user.id] = 0
    player_money[user.id] += amount

    await interaction.response.send_message(
        f"✅ Gave ${amount:,} to {user.display_name}\n"
        f"New balance: ${player_money[user.id]:,}"
    )


@bot.tree.command(name="admin_set_balance", description="[ADMIN] Set a player's exact balance")
@app_commands.describe(
    user="The user",
    amount="New balance amount"
)
@app_commands.checks.has_permissions(administrator=True)
async def admin_set_balance(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Set player balance"""
    player_money[user.id] = amount
    await interaction.response.send_message(f"✅ Set {user.display_name}'s balance to ${amount:,}")


@bot.tree.command(name="admin_view_businesses", description="[ADMIN] View all active businesses and their details")
@app_commands.checks.has_permissions(administrator=True)
async def admin_view_businesses(interaction: discord.Interaction):
    """View all businesses"""
    if not businesses:
        await interaction.response.send_message("❌ No active businesses.")
        return

    embed = discord.Embed(title="📊 All Active Businesses", color=discord.Color.blue())

    for biz_id, biz in businesses.items():
        invested = biz.get("capital_invested", 0)
        field_value = (
            f"Owner: {biz['entrepreneur_name']}\n"
            f"Initial Quality: {biz['initial_quality']}/10\n"
            f"Capital Invested: ${invested:,}\n"
            f"Quality Boost: +{biz.get('quality_boost', 0)}\n"
            f"Final Quality: {biz['final_quality']}/10\n"
            f"Valuation: ${biz['valuation']:,}\n"
            f"Sharks: {', '.join(biz['shark_names'])}\n"
            f"Investment Ready: {'✅' if biz.get('investment_complete') else '⏳ Waiting'}"
        )
        embed.add_field(name=f"🏢 {biz['pitch'][:50]}...", value=field_value, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="admin_start_season", description="[ADMIN] Start a new season")
@app_commands.checks.has_permissions(administrator=True)
async def admin_start_season(interaction: discord.Interaction):
    """Start new season"""
    game_config["season_active"] = True
    game_config["season_start"] = datetime.now()

    # Reset everything
    player_money.clear()
    player_investments.clear()
    businesses.clear()
    eliminated_entrepreneurs.clear()
    leaderboard["entrepreneurs"].clear()
    leaderboard["sharks"].clear()

    await interaction.response.send_message(
        "🎬 **NEW SEASON STARTED!**\n"
        "All data has been reset. Let the pitches begin!"
    )


@bot.tree.command(name="admin_business_report",
                  description="[ADMIN] Generate final business report and determine winners")
@app_commands.checks.has_permissions(administrator=True)
async def admin_business_report(interaction: discord.Interaction):
    """Generate business report"""
    if not businesses:
        await interaction.response.send_message("❌ No businesses to report on!")
        return

    await interaction.response.defer()

    # Calculate outcomes for all businesses
    results = []

    for biz_id, biz in businesses.items():
        success, final_val, multiplier = calculate_business_outcome(biz_id)

        # Calculate payouts
        entrepreneur_equity = 100 - biz["equity_given"]
        entrepreneur_payout = (final_val * entrepreneur_equity / 100) if success else 0

        # Distribute to sharks
        shark_payout_each = (final_val * biz["equity_given"] / 100) / len(biz["shark_ids"]) if success else 0

        # Update player money
        if biz["entrepreneur_id"] in player_money:
            player_money[biz["entrepreneur_id"]] += entrepreneur_payout
        else:
            player_money[biz["entrepreneur_id"]] = entrepreneur_payout

        for shark_id in biz["shark_ids"]:
            if shark_id in player_money:
                player_money[shark_id] += shark_payout_each
            else:
                player_money[shark_id] = shark_payout_each

        results.append({
            "business": biz,
            "success": success,
            "final_valuation": final_val,
            "multiplier": multiplier,
            "entrepreneur_payout": entrepreneur_payout,
            "shark_payout_each": shark_payout_each
        })

    # Create report embed
    report_embed = discord.Embed(
        title="📊 BUSINESS REPORT - SEASON RESULTS",
        description="All businesses have matured. Here are the outcomes:",
        color=discord.Color.gold()
    )

    for i, result in enumerate(results, 1):
        biz = result["business"]
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"

        field_value = (
            f"**Status:** {status}\n"
            f"**Initial Quality:** {biz['initial_quality']}/10\n"
            f"**Final Quality:** {biz['final_quality']}/10\n"
            f"**Capital Invested:** ${biz.get('capital_invested', 0):,}\n"
            f"**Initial Valuation:** ${biz['valuation']:,}\n"
            f"**Final Valuation:** ${result['final_valuation']:,}\n"
        )

        if result["success"]:
            field_value += f"**Growth:** {result['multiplier']:.2f}x\n"
            field_value += f"**Entrepreneur Gained:** ${result['entrepreneur_payout']:,.0f}\n"
            field_value += f"**Each Shark Gained:** ${result['shark_payout_each']:,.0f}\n"

        report_embed.add_field(
            name=f"{i}. {biz['entrepreneur_name']}'s Business",
            value=field_value,
            inline=False
        )

    await interaction.followup.send(embed=report_embed)

    # Generate final leaderboard
    await generate_final_leaderboard(interaction.channel)


async def generate_final_leaderboard(channel):
    """Generate and post final leaderboard"""
    if not player_money:
        await channel.send("❌ No players to rank!")
        return

    # Sort all players by money
    sorted_players = sorted(player_money.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 FINAL LEADERBOARD - RICHEST PLAYERS",
        description="The wealthiest players in the tank!",
        color=discord.Color.gold()
    )

    medals = ["🥇", "🥈", "🥉"]

    for i, (uid, money) in enumerate(sorted_players[:10], 1):
        member = bot.get_user(uid)
        name = member.display_name if member else f"User {uid}"
        medal = medals[i - 1] if i <= 3 else f"{i}."

        embed.add_field(
            name=f"{medal} {name}",
            value=f"💰 ${money:,.0f}",
            inline=False
        )

    await channel.send(embed=embed)


@bot.tree.command(name="admin_end_season", description="[ADMIN] End current season")
@app_commands.checks.has_permissions(administrator=True)
async def admin_end_season(interaction: discord.Interaction):
    """End season"""
    game_config["season_active"] = False
    await interaction.response.send_message("🏁 **SEASON ENDED**\nStart a new season with `/admin_start_season`")


# ========== PLAYER COMMANDS ==========
@bot.tree.command(name="help", description="Show all available commands and how to play")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    is_admin = interaction.user.guild_permissions.administrator
    is_shark = has_role(interaction.user, SHARK_ROLE_ID) if SHARK_ROLE_ID else False
    is_entrepreneur = has_role(interaction.user, ENTREPRENEUR_ROLE_ID) if ENTREPRENEUR_ROLE_ID else False

    embed = discord.Embed(
        title="🦈 Shark Tank Bot - Help Guide",
        description="Welcome to Shark Tank! Here's how to play:",
        color=discord.Color.blue()
    )

    # Game Overview
    embed.add_field(
        name="📖 How It Works",
        value=(
            "**Entrepreneurs** pitch their business ideas to **Sharks** for investment.\n"
            "Sharks invest virtual money, and entrepreneurs use the capital to grow their businesses.\n"
            "After all pitches, businesses are evaluated and the **richest person wins!**"
        ),
        inline=False
    )

    # For Everyone
    embed.add_field(
        name="👥 Commands For Everyone",
        value=(
            "`/help` - Show this help menu\n"
            "`/balance` - Check your money balance\n"
            "`/leaderboard` - View money rankings\n"
            "`/status` - Check if there's an active pitch\n"
        ),
        inline=False
    )

    # For Entrepreneurs
    if is_entrepreneur or is_admin:
        embed.add_field(
            name="👔 Entrepreneur Commands",
            value=(
                "`/pitch <idea> <amount> <equity>` - Pitch your business\n"
                "  Example: `/pitch Mobile App 100000 20`\n"
                "  (Asking $100K for 20% equity)\n\n"
                "During negotiation:\n"
                "• Accept deals from sharks\n"
                "• Decline and negotiate\n"
                "• Counter offer\n"
                "• Walk away (eliminates you!)\n\n"
                "After deal:\n"
                "`/invest <1|2|3>` - Invest capital to improve business (via DM)\n"
                "`/finish_investing` - Stop investing early\n"
            ),
            inline=False
        )

    # For Sharks
    if is_shark or is_admin:
        embed.add_field(
            name="🦈 Shark Commands",
            value=(
                "During pitches, use buttons to:\n"
                "• **Make Offer** - Solo investment\n"
                "• **Joint Offer** - Partner with other sharks\n"
                "• **I'm Out** - Pass on the deal\n\n"
                "You can negotiate back and forth endlessly!\n"
                "Accept entrepreneur counters or make new offers."
            ),
            inline=False
        )

    # For Admins
    if is_admin:
        embed.add_field(
            name="⚙️ Admin Commands",
            value=(
                "`/admin_set_roles` - **REQUIRED FIRST** - Set Shark & Entrepreneur roles\n"
                "`/admin_start_season` - Start a new season\n"
                "`/admin_config` - View current settings\n"
                "`/admin_set_shark_money` - Set starting money for sharks\n"
                "`/admin_set_deadline` - Set investment deadline\n"
                "`/admin_view_businesses` - See all businesses & quality scores\n"
                "`/admin_business_report` - Calculate final results & winners\n"
                "`/admin_end_season` - End the season\n"
                "`/admin_give_money` - Give money to a player\n"
                "`/admin_set_balance` - Set player's exact balance\n"
            ),
            inline=False
        )

    # Investment Tiers
    embed.add_field(
        name="💰 Investment Options (After Getting Deal)",
        value=(
            "**Option 1: Basic Growth** - $25,000 → +1 Quality\n"
            "**Option 2: Moderate Expansion** - $75,000 → +3 Quality\n"
            "**Option 3: Aggressive Scale** - $150,000 → +5 Quality\n\n"
            "Higher quality = better chance of business success!"
        ),
        inline=False
    )

    # Game Flow
    embed.add_field(
        name="🎮 Game Flow",
        value=(
            "1️⃣ Admin starts season with `/admin_start_season`\n"
            "2️⃣ Entrepreneurs pitch one at a time\n"
            "3️⃣ Sharks make offers and negotiate\n"
            "4️⃣ Entrepreneur accepts deal OR walks away (eliminated)\n"
            "5️⃣ Entrepreneur invests capital via DM\n"
            "6️⃣ Repeat until all entrepreneurs have pitched\n"
            "7️⃣ Admin runs `/admin_business_report` to determine winners\n"
            "8️⃣ **Richest person (shark OR entrepreneur) wins!** 🏆\n"
        ),
        inline=False
    )

    # Tips
    embed.add_field(
        name="💡 Pro Tips",
        value=(
            "• **Entrepreneurs:** Negotiate hard to keep more equity!\n"
            "• **Sharks:** Invest wisely - businesses can fail!\n"
            "• **Everyone:** Success is based on hidden quality + investments\n"
            "• Walking away = elimination. No second chances!\n"
        ),
        inline=False
    )

    # Setup warning
    if not SHARK_ROLE_ID or not ENTREPRENEUR_ROLE_ID:
        embed.add_field(
            name="⚠️ Setup Required!",
            value="Admins must run `/admin_set_roles` before the game can start!",
            inline=False
        )

    embed.set_footer(text="Good luck in the tank! 🦈💰")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="balance", description="Check your current balance")
async def balance(interaction: discord.Interaction):
    """Check balance"""
    if interaction.user.id not in player_money:
        await interaction.response.send_message("❌ You haven't participated in any deals yet!", ephemeral=True)
        return

    balance = player_money[interaction.user.id]

    embed = discord.Embed(title="💰 Your Balance", color=discord.Color.green())
    embed.add_field(name="Current Money", value=f"${balance:,}")

    # Show businesses if entrepreneur
    user_businesses = [b for b in businesses.values() if b["entrepreneur_id"] == interaction.user.id]
    if user_businesses:
        biz_text = "\n".join([f"• {b['pitch'][:40]}..." for b in user_businesses])
        embed.add_field(name="Your Businesses", value=biz_text, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="pitch", description="Pitch your business idea to the Sharks")
@app_commands.describe(
    idea="Describe your business idea",
    asking_amount="Amount of money you're asking for (e.g., 100000)",
    asking_equity="Equity percentage you're offering (e.g., 20)"
)
async def slash_pitch(interaction: discord.Interaction, idea: str, asking_amount: int, asking_equity: float):
    """Entrepreneur pitches their idea"""
    # Check if roles are configured
    if not SHARK_ROLE_ID or not ENTREPRENEUR_ROLE_ID:
        await interaction.response.send_message(
            "❌ Game not configured! An admin must run `/admin_set_roles` first.",
            ephemeral=True
        )
        return

    # Check if user has Entrepreneur role
    if not has_role(interaction.user, ENTREPRENEUR_ROLE_ID):
        await interaction.response.send_message("❌ Only users with the **Entrepreneur** role can pitch.",
                                                ephemeral=True)
        return

    # Check if eliminated
    if interaction.user.id in eliminated_entrepreneurs:
        await interaction.response.send_message("❌ You have been eliminated from this season. Better luck next time!",
                                                ephemeral=True)
        return

    # Check if already pitched
    user_businesses = [b for b in businesses.values() if b["entrepreneur_id"] == interaction.user.id]
    if user_businesses:
        await interaction.response.send_message("❌ You have already pitched this season! One pitch per entrepreneur.",
                                                ephemeral=True)
        return

    if round_data["active"]:
        await interaction.response.send_message("❌ A pitch is already active. Please wait for it to conclude.",
                                                ephemeral=True)
        return

    if not game_config["season_active"]:
        await interaction.response.send_message("❌ No season is currently active. Wait for an admin to start one!",
                                                ephemeral=True)
        return

    # Generate random business quality score (hidden from everyone except admin)
    business_quality = random.randint(1, 10)
    business_id = new_business_id()

    round_data.update({
        "active": True,
        "entrepreneur_id": interaction.user.id,
        "entrepreneur_name": interaction.user.display_name,
        "pitch": idea,
        "asking_amount": asking_amount,
        "asking_equity": asking_equity,
        "business_id": business_id,
        "business_quality": business_quality,
        "offers": {},
        "negotiations": []
    })

    ensure_user(leaderboard["entrepreneurs"], interaction.user.id, interaction.user.display_name)
    leaderboard["entrepreneurs"][interaction.user.id]["pitches"] += 1

    add_negotiation_log(interaction.user.display_name, "PITCH", f"Asking ${asking_amount:,} for {asking_equity}%")

    valuation = (asking_amount / asking_equity) * 100

    embed = discord.Embed(
        title="📣 NEW PITCH",
        description=idea,
        color=discord.Color.gold()
    )
    embed.add_field(name="💰 Asking", value=f"${asking_amount:,}", inline=True)
    embed.add_field(name="📊 For Equity", value=f"{asking_equity}%", inline=True)
    embed.add_field(name="💎 Valuation", value=f"${valuation:,.0f}", inline=True)
    embed.set_footer(text=f"Pitched by {interaction.user.display_name} | Business ID: {business_id}")

    await interaction.response.send_message(embed=embed, view=SharkOfferView())


@bot.tree.command(name="leaderboard", description="Display current money leaderboard")
async def slash_leaderboard(interaction: discord.Interaction):
    """Display leaderboard"""
    if not player_money:
        await interaction.response.send_message("❌ No players have money yet!")
        return

    sorted_players = sorted(player_money.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 MONEY LEADERBOARD", color=discord.Color.blue())

    medals = ["🥇", "🥈", "🥉"]

    for i, (uid, money) in enumerate(sorted_players[:10], 1):
        member = interaction.guild.get_member(uid)
        name = member.display_name if member else f"User {uid}"
        medal = medals[i - 1] if i <= 3 else f"{i}."

        embed.add_field(
            name=f"{medal} {name}",
            value=f"💰 ${money:,}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="status", description="Check current pitch status")
async def slash_status(interaction: discord.Interaction):
    """Check status"""
    if round_data["active"]:
        embed = discord.Embed(
            title="📊 Active Pitch",
            description=round_data["pitch"],
            color=discord.Color.orange()
        )
        embed.add_field(name="Entrepreneur", value=round_data["entrepreneur_name"])
        embed.add_field(name="Asking", value=f"${round_data['asking_amount']:,} for {round_data['asking_equity']}%")
        embed.add_field(name="Active Offers",
                        value=str(len([o for o in round_data["offers"].values() if o.get("active")])))

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("✅ No active pitch. Entrepreneurs can start pitching!")


# ========== SHARK OFFER SYSTEM ==========
class SharkOfferView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction):
        # Check if roles configured
        if not SHARK_ROLE_ID:
            await interaction.response.send_message("❌ Game not configured yet!", ephemeral=True)
            return False

        if not has_role(interaction.user, SHARK_ROLE_ID):
            await interaction.response.send_message("❌ Only users with the **Shark** role can make offers.",
                                                    ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💰 Make Offer", style=discord.ButtonStyle.green, custom_id="solo_offer")
    async def solo(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if shark has enough money
        ensure_player_money(interaction.user.id, is_shark=True)
        await interaction.response.send_modal(SoloOfferModal())

    @discord.ui.button(label="🤝 Joint Offer", style=discord.ButtonStyle.blurple, custom_id="joint_offer")
    async def joint(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_player_money(interaction.user.id, is_shark=True)
        await interaction.response.send_message(
            "Select sharks to combine with:",
            view=JointOfferView(interaction.guild, interaction.user.id),
            ephemeral=True
        )

    @discord.ui.button(label="🚫 I'm Out", style=discord.ButtonStyle.secondary, custom_id="im_out")
    async def im_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        add_negotiation_log(interaction.user.display_name, "OUT", "Declined to invest")
        await interaction.response.send_message(
            f"🚫 **{interaction.user.display_name}** is OUT!",
            ephemeral=False
        )


# ========== SOLO OFFER MODAL ==========
class SoloOfferModal(discord.ui.Modal, title="💰 Shark Offer"):
    amount = discord.ui.TextInput(label="Investment Amount", placeholder="e.g., 100000")
    equity = discord.ui.TextInput(label="Equity %", placeholder="e.g., 25")
    conditions = discord.ui.TextInput(
        label="Conditions (Optional)",
        required=False,
        placeholder="e.g., Must hire CFO, Advisory role",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        amount_val = float(self.amount.value.replace("$", "").replace(",", ""))
        equity_val = float(self.equity.value.replace("%", ""))

        # Check if shark has enough money
        if player_money.get(interaction.user.id, 0) < amount_val:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have ${player_money.get(interaction.user.id, 0):,} but need ${amount_val:,}",
                ephemeral=True
            )
            return

        offer_id = new_offer_id()

        round_data["offers"][offer_id] = {
            "sharks": [interaction.user.id],
            "shark_names": [interaction.user.display_name],
            "amount": amount_val,
            "equity": equity_val,
            "conditions": self.conditions.value or "None",
            "active": True,
            "pending": False
        }

        add_negotiation_log(
            interaction.user.display_name,
            "OFFER",
            f"${amount_val:,} for {equity_val}%"
        )

        await interaction.response.send_message("✅ Offer submitted.", ephemeral=True)
        await print_offer(interaction.channel, offer_id)


# ========== JOINT OFFER UI ==========
class SharkSelect(discord.ui.Select):
    def __init__(self, guild, initiator_id):
        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id))
            for m in guild.members
            if has_role(m, SHARK_ROLE_ID) and m.id != initiator_id
        ]

        if not options:
            options = [discord.SelectOption(label="No other sharks available", value="none")]

        super().__init__(
            placeholder="Select Sharks",
            min_values=1,
            max_values=min(len(options), 25),
            options=options,
            custom_id="shark_select"
        )

    async def callback(self, interaction):
        if self.values[0] != "none":
            self.view.selected = [int(v) for v in self.values]
            await interaction.response.send_message("✅ Sharks selected. Click Continue.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No other sharks available.", ephemeral=True)


class JointOfferView(discord.ui.View):
    def __init__(self, guild, initiator_id):
        super().__init__(timeout=120)
        self.selected = []
        self.initiator_id = initiator_id
        self.add_item(SharkSelect(guild, initiator_id))

    @discord.ui.button(label="➡ Continue", style=discord.ButtonStyle.success, custom_id="continue_joint")
    async def cont(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected:
            return await interaction.response.send_message("❌ Select sharks first.", ephemeral=True)

        all_sharks = [interaction.user.id] + self.selected
        await interaction.response.send_modal(JointOfferModal(all_sharks, interaction.guild))


class JointOfferModal(discord.ui.Modal):
    def __init__(self, shark_ids, guild):
        super().__init__(title="🤝 Combined Offer")
        self.shark_ids = shark_ids
        self.guild = guild

        self.amount = discord.ui.TextInput(label="Total Investment", placeholder="e.g., 200000")
        self.equity = discord.ui.TextInput(label="Total Equity %", placeholder="e.g., 30")
        self.conditions = discord.ui.TextInput(
            label="Conditions (Optional)",
            required=False,
            placeholder="e.g., Must relocate, Split equity 50/50",
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.amount)
        self.add_item(self.equity)
        self.add_item(self.conditions)

    async def on_submit(self, interaction: discord.Interaction):
        offer_id = new_offer_id()
        names = [self.guild.get_member(sid).display_name for sid in self.shark_ids]
        amount_val = float(self.amount.value.replace("$", "").replace(",", ""))
        equity_val = float(self.equity.value.replace("%", ""))

        # Check if all sharks have enough money (split evenly)
        amount_per_shark = amount_val / len(self.shark_ids)
        for sid in self.shark_ids:
            if player_money.get(sid, 0) < amount_per_shark:
                await interaction.response.send_message(
                    f"❌ One or more sharks don't have enough funds! Need ${amount_per_shark:,} each.",
                    ephemeral=True
                )
                return

        round_data["offers"][offer_id] = {
            "sharks": self.shark_ids,
            "shark_names": names,
            "amount": amount_val,
            "equity": equity_val,
            "conditions": self.conditions.value or "None",
            "active": False,
            "pending": True,
            "consent": {sid: False for sid in self.shark_ids}
        }

        round_data["offers"][offer_id]["consent"][interaction.user.id] = True

        add_negotiation_log(
            ", ".join(names),
            "JOINT OFFER (Pending)",
            f"${amount_val:,} for {equity_val}%"
        )

        await interaction.response.send_message(
            "🤝 Joint offer created. Awaiting other shark approvals...",
            ephemeral=True
        )

        await interaction.channel.send(
            f"🦈 **Joint Offer Pending Approval**\n"
            f"Sharks: {', '.join(names)}\n"
            f"Initiator {interaction.user.display_name} has already approved.",
            view=SharkConsentView(offer_id)
        )


class SharkConsentView(discord.ui.View):
    def __init__(self, offer_id):
        super().__init__(timeout=300)
        self.offer_id = offer_id

    async def interaction_check(self, interaction):
        offer = round_data["offers"].get(self.offer_id)
        if not offer:
            await interaction.response.send_message("❌ This offer is no longer valid.", ephemeral=True)
            return False

        if interaction.user.id not in offer["sharks"]:
            await interaction.response.send_message("❌ Only sharks in this joint offer can respond.", ephemeral=True)
            return False

        if offer["consent"].get(interaction.user.id, False):
            await interaction.response.send_message("❌ You have already approved this offer.", ephemeral=True)
            return False

        return True

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="approve_joint")
    async def approve(self, interaction, button):
        offer = round_data["offers"][self.offer_id]
        offer["consent"][interaction.user.id] = True

        await interaction.response.send_message("✅ You approved the joint offer.", ephemeral=True)

        if all(offer["consent"].values()):
            offer["pending"] = False
            offer["active"] = True

            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)

            add_negotiation_log(
                ", ".join(offer["shark_names"]),
                "JOINT OFFER APPROVED",
                f"${offer['amount']:,} for {offer['equity']}%"
            )

            await interaction.channel.send("🤝 **ALL SHARKS APPROVED THE JOINT OFFER!**")
            await print_offer(interaction.channel, self.offer_id)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, custom_id="decline_joint")
    async def decline(self, interaction, button):
        offer = round_data["offers"][self.offer_id]
        offer["pending"] = False
        offer["active"] = False

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        add_negotiation_log(interaction.user.display_name, "DECLINED JOINT", "Refused to join offer")
        await interaction.channel.send(f"❌ **Joint offer cancelled.** {interaction.user.display_name} declined.")


# ========== OFFER DISPLAY ==========
async def print_offer(channel, offer_id):
    offer = round_data["offers"][offer_id]
    valuation = (offer["amount"] / offer["equity"]) * 100

    embed = discord.Embed(title="💼 SHARK OFFER", color=discord.Color.green())
    embed.add_field(name="🦈 Sharks", value=", ".join(offer["shark_names"]), inline=False)
    embed.add_field(name="💰 Amount", value=f"${offer['amount']:,}", inline=True)
    embed.add_field(name="📊 Equity", value=f"{offer['equity']}%", inline=True)
    embed.add_field(name="💎 Valuation", value=f"${valuation:,.0f}", inline=True)
    embed.add_field(name="📜 Conditions", value=offer["conditions"], inline=False)

    if round_data["asking_amount"] and round_data["asking_equity"]:
        original_val = (round_data["asking_amount"] / round_data["asking_equity"]) * 100
        embed.add_field(
            name="📍 Original Ask",
            value=f"${round_data['asking_amount']:,} for {round_data['asking_equity']}% (${original_val:,.0f} valuation)",
            inline=False
        )

    await channel.send(embed=embed, view=EntrepreneurDecisionView(offer_id))


# ========== ENTREPRENEUR DECISION ==========
class EntrepreneurDecisionView(discord.ui.View):
    def __init__(self, offer_id):
        super().__init__(timeout=None)
        self.offer_id = offer_id

    async def interaction_check(self, interaction):
        if interaction.user.id != round_data["entrepreneur_id"]:
            await interaction.response.send_message("❌ Only the entrepreneur can respond to offers.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Accept Deal", style=discord.ButtonStyle.success, custom_id="accept_deal")
    async def accept(self, interaction, button):
        offer = round_data["offers"][self.offer_id]

        # Deduct money from sharks
        amount_per_shark = offer["amount"] / len(offer["sharks"])
        for sid in offer["sharks"]:
            player_money[sid] -= amount_per_shark

        # Give money to entrepreneur
        if interaction.user.id not in player_money:
            player_money[interaction.user.id] = 0
        player_money[interaction.user.id] += offer["amount"]

        # Create business record
        valuation = (offer["amount"] / offer["equity"]) * 100

        businesses[round_data["business_id"]] = {
            "entrepreneur_id": interaction.user.id,
            "entrepreneur_name": interaction.user.display_name,
            "pitch": round_data["pitch"],
            "shark_ids": offer["sharks"],
            "shark_names": offer["shark_names"],
            "investment": offer["amount"],
            "equity_given": offer["equity"],
            "valuation": valuation,
            "initial_quality": round_data["business_quality"],
            "capital_invested": 0,
            "quality_boost": 0,
            "final_quality": round_data["business_quality"],
            "investment_complete": False,
            "deadline": datetime.now() + timedelta(hours=game_config["investment_deadline_hours"])
        }

        # Update leaderboard
        leaderboard["entrepreneurs"][interaction.user.id]["deals"] += 1
        for sid in offer["sharks"]:
            ensure_user(leaderboard["sharks"], sid, interaction.guild.get_member(sid).display_name)
            leaderboard["sharks"][sid]["invested"] += 1

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        round_data["active"] = False

        add_negotiation_log(
            round_data["entrepreneur_name"],
            "DEAL ACCEPTED",
            f"${offer['amount']:,} for {offer['equity']}%"
        )

        embed = discord.Embed(
            title="🎉 DEAL CLOSED!",
            description=f"**{round_data['entrepreneur_name']}** accepted the offer from **{', '.join(offer['shark_names'])}**",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Investment", value=f"${offer['amount']:,}")
        embed.add_field(name="📊 Equity", value=f"{offer['equity']}%")
        embed.add_field(name="💎 Valuation", value=f"${valuation:,.0f}")

        await interaction.response.send_message(embed=embed)

        # Send DM to entrepreneur for investment phase
        try:
            await send_investment_dm(interaction.user, round_data["business_id"])
        except:
            await interaction.channel.send(
                f"⚠️ {interaction.user.mention} - I couldn't DM you! Please enable DMs and use `/check_investments` to see your options."
            )

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, custom_id="reject_offer")
    async def reject(self, interaction, button):
        offer = round_data["offers"][self.offer_id]
        offer["active"] = False

        button.disabled = True
        await interaction.message.edit(view=self)

        add_negotiation_log(
            round_data["entrepreneur_name"],
            "DECLINED OFFER",
            f"Rejected ${offer['amount']:,} for {offer['equity']}%"
        )

        await interaction.response.send_message(
            f"❌ **Offer declined by {interaction.user.display_name}**\n"
            "💬 Negotiations continue!",
            ephemeral=False
        )

    @discord.ui.button(label="💬 Counter Offer", style=discord.ButtonStyle.primary, custom_id="counter_offer")
    async def counter(self, interaction, button):
        await interaction.response.send_modal(CounterOfferModal(self.offer_id))

    @discord.ui.button(label="🛑 Walk Away", style=discord.ButtonStyle.secondary, custom_id="withdraw_pitch")
    async def withdraw(self, interaction, button):
        leaderboard["entrepreneurs"][round_data["entrepreneur_id"]]["rejected"] += 1
        eliminated_entrepreneurs.add(interaction.user.id)

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        round_data["active"] = False

        add_negotiation_log(round_data["entrepreneur_name"], "WALKED AWAY - ELIMINATED", "No deal reached")

        embed = discord.Embed(
            title="🛑 NO DEAL - ELIMINATED",
            description=f"**{round_data['entrepreneur_name']}** has walked away and is ELIMINATED from this season!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)


# ========== COUNTER OFFER ==========
class CounterOfferModal(discord.ui.Modal, title="💬 Counter Offer"):
    def __init__(self, original_offer_id):
        super().__init__()
        self.original_offer_id = original_offer_id

        self.amount = discord.ui.TextInput(label="Counter Amount", placeholder="e.g., 150000")
        self.equity = discord.ui.TextInput(label="Counter Equity %", placeholder="e.g., 20")
        self.message = discord.ui.TextInput(
            label="Message to Sharks",
            required=False,
            placeholder="Explain your counter...",
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.amount)
        self.add_item(self.equity)
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        original_offer = round_data["offers"][self.original_offer_id]
        original_offer["active"] = False

        amount_val = float(self.amount.value.replace("$", "").replace(",", ""))
        equity_val = float(self.equity.value.replace("%", ""))

        add_negotiation_log(
            round_data["entrepreneur_name"],
            "COUNTER OFFER",
            f"${amount_val:,} for {equity_val}% | {self.message.value or 'No message'}"
        )

        embed = discord.Embed(
            title="💬 ENTREPRENEUR COUNTER OFFER",
            description=self.message.value or f"Counter to {', '.join(original_offer['shark_names'])}",
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Requesting", value=f"${amount_val:,}", inline=True)
        embed.add_field(name="📊 For Equity", value=f"{equity_val}%", inline=True)
        embed.add_field(name="💎 Valuation", value=f"${(amount_val / equity_val * 100):,.0f}", inline=True)
        embed.add_field(
            name="📍 Original Offer",
            value=f"${original_offer['amount']:,} for {original_offer['equity']}%",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=SharkCounterResponseView(
                original_offer["sharks"],
                amount_val,
                equity_val,
                self.original_offer_id
            )
        )


class SharkCounterResponseView(discord.ui.View):
    def __init__(self, shark_ids, counter_amount, counter_equity, original_offer_id):
        super().__init__(timeout=None)
        self.shark_ids = shark_ids
        self.counter_amount = counter_amount
        self.counter_equity = counter_equity
        self.original_offer_id = original_offer_id

    async def interaction_check(self, interaction):
        if not has_role(interaction.user, SHARK_ROLE_ID):
            await interaction.response.send_message("❌ Only Sharks can respond.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Accept Counter", style=discord.ButtonStyle.success, custom_id="accept_counter")
    async def accept_counter(self, interaction, button):
        if player_money.get(interaction.user.id, 0) < self.counter_amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have ${player_money.get(interaction.user.id, 0):,}",
                ephemeral=True
            )
            return

        offer_id = new_offer_id()

        round_data["offers"][offer_id] = {
            "sharks": [interaction.user.id],
            "shark_names": [interaction.user.display_name],
            "amount": self.counter_amount,
            "equity": self.counter_equity,
            "conditions": "Accepted entrepreneur's counter",
            "active": True,
            "pending": False
        }

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        add_negotiation_log(
            interaction.user.display_name,
            "ACCEPTED COUNTER",
            f"${self.counter_amount:,} for {self.counter_equity}%"
        )

        await interaction.response.send_message(
            f"✅ **{interaction.user.display_name} accepts the counter offer!**"
        )
        await print_offer(interaction.channel, offer_id)

    @discord.ui.button(label="💬 Counter Back", style=discord.ButtonStyle.primary, custom_id="counter_back")
    async def counter_back(self, interaction, button):
        await interaction.response.send_modal(SoloOfferModal())

    @discord.ui.button(label="❌ Decline Counter", style=discord.ButtonStyle.danger, custom_id="decline_counter")
    async def decline_counter(self, interaction, button):
        add_negotiation_log(
            interaction.user.display_name,
            "DECLINED COUNTER",
            "Rejected entrepreneur's counter"
        )

        await interaction.response.send_message(
            f"❌ **{interaction.user.display_name} declines the counter.**\n"
            "💬 Negotiations continue!",
            ephemeral=False
        )


# ========== DM INVESTMENT SYSTEM ==========
async def send_investment_dm(user, business_id):
    """Send investment options to entrepreneur via DM"""
    business = businesses[business_id]
    capital = business["investment"]

    embed = discord.Embed(
        title="💰 INVESTMENT PHASE - BUILD YOUR BUSINESS",
        description=f"You received **${capital:,}** from the deal!\n\nNow it's time to invest this capital to improve your business quality score and increase your chances of success.",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📊 Current Status",
        value=f"Available Capital: ${capital:,}\nDeadline: {business['deadline'].strftime('%Y-%m-%d %H:%M')} UTC",
        inline=False
    )

    embed.add_field(
        name="💡 Investment Options",
        value=(
            "**1️⃣ Basic Growth** - $25,000\n"
            "   → +1 Business Quality\n\n"
            "**2️⃣ Moderate Expansion** - $75,000\n"
            "   → +3 Business Quality\n\n"
            "**3️⃣ Aggressive Scale** - $150,000\n"
            "   → +5 Business Quality\n\n"
            "You can invest multiple times until your capital runs out!\n"
            "Use `/invest <option_number>` to invest."
        ),
        inline=False
    )

    embed.set_footer(text="Tip: Higher quality = better chance of success!")

    await user.send(embed=embed)


@bot.tree.command(name="invest", description="Invest your capital to improve business quality")
@app_commands.describe(option="Choose 1 (Basic), 2 (Moderate), or 3 (Aggressive)")
async def invest_command(interaction: discord.Interaction, option: int):
    """Invest capital"""
    # Find user's business
    user_business = None
    business_id = None

    for bid, biz in businesses.items():
        if biz["entrepreneur_id"] == interaction.user.id and not biz["investment_complete"]:
            user_business = biz
            business_id = bid
            break

    if not user_business:
        await interaction.response.send_message("❌ You don't have an active business to invest in!", ephemeral=True)
        return

    if option not in [1, 2, 3]:
        await interaction.response.send_message("❌ Invalid option! Choose 1, 2, or 3.", ephemeral=True)
        return

    tier = INVESTMENT_TIERS[str(option)]
    available_capital = user_business["investment"] - user_business["capital_invested"]

    if available_capital < tier["cost"]:
        await interaction.response.send_message(
            f"❌ Insufficient capital! You have ${available_capital:,} but need ${tier['cost']:,}\n"
            f"Remaining capital will be added to your balance.",
            ephemeral=True
        )
        return

    # Make investment
    user_business["capital_invested"] += tier["cost"]
    user_business["quality_boost"] += tier["quality_boost"]
    user_business["final_quality"] = user_business["initial_quality"] + user_business["quality_boost"]

    remaining = user_business["investment"] - user_business["capital_invested"]

    embed = discord.Embed(
        title="✅ Investment Made!",
        description=f"You invested in **{tier['name']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Cost", value=f"${tier['cost']:,}")
    embed.add_field(name="Quality Boost", value=f"+{tier['quality_boost']}")
    embed.add_field(name="Remaining Capital", value=f"${remaining:,}")
    embed.add_field(name="Total Quality Boost", value=f"+{user_business['quality_boost']}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

    if remaining < 25000:  # Can't afford any more investments
        user_business["investment_complete"] = True
        player_money[interaction.user.id] += remaining  # Add leftover to balance

        await interaction.followup.send(
            f"✅ **Investment phase complete!**\n"
            f"Remaining ${remaining:,} added to your balance.\n"
            f"Your business will be evaluated in the final report!",
            ephemeral=True
        )


@bot.tree.command(name="finish_investing", description="Finish investing and save remaining capital")
async def finish_investing(interaction: discord.Interaction):
    """Finish investment phase early"""
    user_business = None

    for bid, biz in businesses.items():
        if biz["entrepreneur_id"] == interaction.user.id and not biz["investment_complete"]:
            user_business = biz
            break

    if not user_business:
        await interaction.response.send_message("❌ No active investment phase!", ephemeral=True)
        return

    remaining = user_business["investment"] - user_business["capital_invested"]
    user_business["investment_complete"] = True
    player_money[interaction.user.id] += remaining

    await interaction.response.send_message(
        f"✅ **Investment complete!**\n"
        f"${remaining:,} added to your balance.\n"
        f"Total quality boost: +{user_business['quality_boost']}",
        ephemeral=True
    )


# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    print(f"Shark Role ID: {SHARK_ROLE_ID if SHARK_ROLE_ID else 'Not set - use /admin_set_roles'}")
    print(f"Entrepreneur Role ID: {ENTREPRENEUR_ROLE_ID if ENTREPRENEUR_ROLE_ID else 'Not set - use /admin_set_roles'}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
        print(f"\n{'=' * 50}")
        print(f"🦈 SHARK TANK BOT READY!")
        print(f"{'=' * 50}")
        if not SHARK_ROLE_ID or not ENTREPRENEUR_ROLE_ID:
            print(f"⚠️  SETUP REQUIRED: Run /admin_set_roles in Discord")
        print(f"{'=' * 50}\n")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


# ========== RUN ==========
bot.run(TOKEN)