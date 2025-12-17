import discord
from discord import app_commands
from discord.ext import commands, tasks
import uuid
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import our custom modules
from database import SharkTankDB
from ipo_system import IPOSystem

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

# Initialize database and IPO system
db = SharkTankDB()
ipo_system = IPOSystem(db)

# ========== GAME CONFIG (Modifiable by Admins) ==========
game_config = {
    "shark_starting_money": 1000000,
    "entrepreneur_starting_money": 0,
    "season_active": False,
    "season_id": None,
    "season_start": None,
    "investment_deadline_hours": 48,
    "quality_range_min": 1,
    "quality_range_max": 10,
    "event_channel_id": None
}

# Investment pricing tiers
INVESTMENT_TIERS = {
    "1": {"cost": 10000, "quality_boost": 1, "name": "Basic Growth"},
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
    "business_quality": None,  # Hidden score
    "offers": {},
    "negotiations": []
}

leaderboard = {
    "entrepreneurs": {},
    "sharks": {}
}


# ========== EVENT LOGGING ==========
async def log_event(guild, event_type: str, description: str, embed: discord.Embed = None):
    """Log important events to the designated channel"""
    if not game_config["event_channel_id"]:
        return

    channel = guild.get_channel(game_config["event_channel_id"])
    if not channel:
        return

    if embed:
        await channel.send(embed=embed)
    else:
        event_embed = discord.Embed(
            title=f"📢 {event_type}",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await channel.send(embed=event_embed)


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
            player_money[uid] = game_config["entrepreneur_starting_money"]

        # Update in database
        if game_config["season_id"]:
            role = "shark" if is_shark else "entrepreneur"
            db.upsert_player(uid, "Unknown", 0, game_config["season_id"], role, player_money[uid])


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

    # Log to database if business exists
    if round_data.get("business_id"):
        db.add_negotiation(round_data["business_id"], actor, action, details)


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


# ========== BACKGROUND TASKS ==========
@tasks.loop(hours=1)
async def check_ipo_expirations():
    """Check for expired IPOs every hour"""
    if not game_config["season_active"] or not game_config["season_id"]:
        return

    closed_ipos = ipo_system.check_expired_ipos(game_config["season_id"])

    for ipo_id in closed_ipos:
        ipo = ipo_system.get_ipo(ipo_id)
        if ipo and game_config["event_channel_id"]:
            for guild in bot.guilds:
                channel = guild.get_channel(game_config["event_channel_id"])
                if channel:
                    await channel.send(f"⏰ **IPO #{ipo_id} has automatically closed** (time expired)")


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
    embed.add_field(name="💼 Entrepreneur Role", value=entrepreneur_role.mention, inline=False)
    embed.set_footer(text="Players with these roles can now participate!")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="admin_set_event_channel", description="[ADMIN] Set channel for event logging")
@app_commands.describe(channel="Channel where events will be logged")
@app_commands.checks.has_permissions(administrator=True)
async def admin_set_event_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set event logging channel"""
    game_config["event_channel_id"] = channel.id
    db.set_event_channel(interaction.guild.id, channel.id)

    embed = discord.Embed(
        title="✅ Event Channel Configured",
        description=f"All important events will be logged to {channel.mention}",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed)

    # Send test message
    test_embed = discord.Embed(
        title="📢 Event Logging Started",
        description="This channel will now receive updates about:\n• Pitches submitted\n• Deals closed\n• Investments made\n• IPO activities\n• Leaderboard updates",
        color=discord.Color.blue()
    )
    await channel.send(embed=test_embed)


@bot.tree.command(name="admin_configure_season", description="[ADMIN] Configure season settings before starting")
@app_commands.describe(
    shark_money="Starting money for sharks",
    entrepreneur_money="Starting money for entrepreneurs",
    investment_deadline="Hours after deal for entrepreneurs to invest",
    quality_min="Minimum business quality score",
    quality_max="Maximum business quality score"
)
@app_commands.checks.has_permissions(administrator=True)
async def admin_configure_season(
        interaction: discord.Interaction,
        shark_money: int = 1000000,
        entrepreneur_money: int = 0,
        investment_deadline: int = 48,
        quality_min: int = 1,
        quality_max: int = 10
):
    """Configure season settings"""
    game_config["shark_starting_money"] = shark_money
    game_config["entrepreneur_starting_money"] = entrepreneur_money
    game_config["investment_deadline_hours"] = investment_deadline
    game_config["quality_range_min"] = quality_min
    game_config["quality_range_max"] = quality_max

    embed = discord.Embed(
        title="⚙️ Season Settings Configured",
        description="These settings will apply when you start the season",
        color=discord.Color.blue()
    )

    embed.add_field(name="💰 Shark Starting Money", value=f"${shark_money:,}", inline=True)
    embed.add_field(name="💵 Entrepreneur Starting Money", value=f"${entrepreneur_money:,}", inline=True)
    embed.add_field(name="⏰ Investment Deadline", value=f"{investment_deadline} hours", inline=True)
    embed.add_field(name="📊 Quality Range", value=f"{quality_min} - {quality_max}", inline=True)

    embed.set_footer(text="Use /admin_start_season to begin with these settings")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="admin_config", description="[ADMIN] View current game configuration")
@app_commands.checks.has_permissions(administrator=True)
async def admin_config(interaction: discord.Interaction):
    """View game config"""
    embed = discord.Embed(title="⚙️ Game Configuration", color=discord.Color.blue())

    # Role info
    shark_role = interaction.guild.get_role(SHARK_ROLE_ID) if SHARK_ROLE_ID else None
    entrepreneur_role = interaction.guild.get_role(ENTREPRENEUR_ROLE_ID) if ENTREPRENEUR_ROLE_ID else None
    event_channel = interaction.guild.get_channel(game_config["event_channel_id"]) if game_config[
        "event_channel_id"] else None

    embed.add_field(
        name="🦈 Shark Role",
        value=shark_role.mention if shark_role else "❌ Not set",
        inline=False
    )
    embed.add_field(
        name="💼 Entrepreneur Role",
        value=entrepreneur_role.mention if entrepreneur_role else "❌ Not set",
        inline=False
    )
    embed.add_field(
        name="📢 Event Channel",
        value=event_channel.mention if event_channel else "❌ Not set",
        inline=False
    )

    embed.add_field(name="Shark Starting Money", value=f"${game_config['shark_starting_money']:,}")
    embed.add_field(name="Entrepreneur Starting Money", value=f"${game_config['entrepreneur_starting_money']:,}")
    embed.add_field(name="Investment Deadline", value=f"{game_config['investment_deadline_hours']} hours")
    embed.add_field(name="Quality Range",
                    value=f"{game_config['quality_range_min']}-{game_config['quality_range_max']}")
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


@bot.tree.command(name="admin_view_business", description="[ADMIN] View detailed business information (private)")
@app_commands.describe(business_id="The business ID to view")
@app_commands.checks.has_permissions(administrator=True)
async def admin_view_business(interaction: discord.Interaction, business_id: str):
    """View detailed business info"""
    if business_id not in businesses:
        await interaction.response.send_message("❌ Business not found!", ephemeral=True)
        return

    biz = businesses[business_id]

    embed = discord.Embed(
        title=f"🔍 Business Details (Admin Only)",
        description=biz['pitch'][:200],
        color=discord.Color.blue()
    )

    embed.add_field(name="Business ID", value=business_id, inline=False)
    embed.add_field(name="Entrepreneur", value=biz['entrepreneur_name'], inline=True)
    embed.add_field(name="Valuation", value=f"${biz['valuation']:,}", inline=True)
    embed.add_field(name="Equity Given", value=f"{biz['equity_given']}%", inline=True)

    embed.add_field(name="🎲 Initial Quality (Hidden)", value=f"{biz['initial_quality']}/10", inline=True)
    embed.add_field(name="📈 Quality Boost", value=f"+{biz.get('quality_boost', 0)}", inline=True)
    embed.add_field(name="✨ Final Quality", value=f"{biz['final_quality']}/10", inline=True)

    embed.add_field(name="Capital Invested", value=f"${biz.get('capital_invested', 0):,}", inline=True)
    embed.add_field(name="Investment Complete", value="✅" if biz.get('investment_complete') else "⏳", inline=True)

    if biz.get('deadline'):
        embed.add_field(name="Deadline", value=biz['deadline'].strftime('%Y-%m-%d %H:%M UTC'), inline=True)

    embed.add_field(name="Sharks", value=", ".join(biz['shark_names']), inline=False)

    # Get investments from database
    investments = db.get_business_investments(business_id)
    if investments:
        inv_text = "\n".join(
            [f"• {inv['shark_name']}: ${inv['amount']:,} for {inv['equity_percentage']}%" for inv in investments])
        embed.add_field(name="Investment Details", value=inv_text, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="admin_reveal_quality", description="[ADMIN] Reveal quality range to everyone")
@app_commands.checks.has_permissions(administrator=True)
async def admin_reveal_quality(interaction: discord.Interaction):
    """Reveal quality range"""
    embed = discord.Embed(
        title="📊 Business Quality System Revealed",
        description="Here's how the hidden quality system works:",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="Quality Range",
        value=f"All businesses are assigned a secret quality score between **{game_config['quality_range_min']}** and **{game_config['quality_range_max']}**",
        inline=False
    )

    embed.add_field(
        name="How It Affects Success",
        value="• Each quality point = 10% success chance\n• Higher quality = higher valuation multiplier on success\n• Entrepreneurs can improve quality by investing capital",
        inline=False
    )

    embed.add_field(
        name="Investment Impact",
        value="• Basic Growth: +1 quality\n• Moderate Expansion: +3 quality\n• Aggressive Scale: +5 quality",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

    # Log event
    await log_event(interaction.guild, "Quality System Revealed",
                    "Admin has revealed the quality scoring system to all players")


@bot.tree.command(name="admin_penalize", description="[ADMIN] Penalize a player (money/reputation)")
@app_commands.describe(
    user="Player to penalize",
    money_penalty="Amount of money to deduct",
    reputation_penalty="Reputation points to deduct",
    reason="Reason for penalty"
)
@app_commands.checks.has_permissions(administrator=True)
async def admin_penalize(
        interaction: discord.Interaction,
        user: discord.Member,
        money_penalty: int = 0,
        reputation_penalty: int = 0,
        reason: str = "Administrative penalty"
):
    """Penalize a player"""
    if not game_config["season_active"]:
        await interaction.response.send_message("❌ No active season!", ephemeral=True)
        return

    # Apply money penalty
    if money_penalty > 0:
        if user.id in player_money:
            player_money[user.id] = max(0, player_money[user.id] - money_penalty)
            db.update_player_balance(user.id, game_config["season_id"], player_money[user.id])

    # Apply reputation penalty
    if reputation_penalty > 0:
        db.add_reputation_event(
            game_config["season_id"],
            user.id,
            "penalty",
            -reputation_penalty,
            reason,
            interaction.user.id
        )

    embed = discord.Embed(
        title="⚠️ Player Penalized",
        description=f"{user.mention} has been penalized",
        color=discord.Color.red()
    )

    if money_penalty > 0:
        embed.add_field(name="Money Penalty", value=f"-${money_penalty:,}", inline=True)
    if reputation_penalty > 0:
        embed.add_field(name="Reputation Penalty", value=f"-{reputation_penalty} points", inline=True)

    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Penalized by {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)

    # Log event
    await log_event(interaction.guild, "Player Penalized", f"{user.display_name} penalized: {reason}")


@bot.tree.command(name="admin_start_season", description="[ADMIN] Start a new season")
@app_commands.checks.has_permissions(administrator=True)
async def admin_start_season(interaction: discord.Interaction):
    """Start new season"""
    # Create season in database
    season_settings = {
        "shark_starting_money": game_config["shark_starting_money"],
        "entrepreneur_starting_money": game_config["entrepreneur_starting_money"],
        "investment_deadline_hours": game_config["investment_deadline_hours"],
        "quality_range_min": game_config["quality_range_min"],
        "quality_range_max": game_config["quality_range_max"]
    }

    season_id = db.create_season(interaction.guild.id, season_settings)

    game_config["season_active"] = True
    game_config["season_id"] = season_id
    game_config["season_start"] = datetime.now()

    # Reset everything
    player_money.clear()
    player_investments.clear()
    businesses.clear()
    eliminated_entrepreneurs.clear()
    leaderboard["entrepreneurs"].clear()
    leaderboard["sharks"].clear()

    embed = discord.Embed(
        title="🎬 NEW SEASON STARTED!",
        description="All data has been reset. Let the pitches begin!",
        color=discord.Color.gold()
    )

    embed.add_field(name="Season ID", value=f"#{season_id}", inline=True)
    embed.add_field(name="Shark Starting Money", value=f"${game_config['shark_starting_money']:,}", inline=True)
    embed.add_field(name="Entrepreneur Starting Money", value=f"${game_config['entrepreneur_starting_money']:,}",
                    inline=True)
    embed.add_field(name="Quality Range",
                    value=f"{game_config['quality_range_min']}-{game_config['quality_range_max']}", inline=True)
    embed.add_field(name="Investment Deadline", value=f"{game_config['investment_deadline_hours']} hours", inline=True)

    embed.set_footer(text="Good luck to all players! 🦈")

    await interaction.response.send_message(embed=embed)

    # Log event
    await log_event(interaction.guild, "Season Started", f"Season #{season_id} has begun!")


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

        # Update database
        outcome_status = "success" if success else "failure"
        db.update_business_outcome(biz_id, outcome_status, final_val)

        # Update player balances in database
        if game_config["season_id"]:
            db.update_player_balance(biz["entrepreneur_id"], game_config["season_id"],
                                     player_money[biz["entrepreneur_id"]])
            for shark_id in biz["shark_ids"]:
                db.update_player_balance(shark_id, game_config["season_id"], player_money[shark_id])

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

    # Log event
    await log_event(interaction.guild, "Business Report Generated", "Final season results have been calculated!")


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

        # Get reputation if available
        rep_text = ""
        if game_config["season_id"]:
            player = db.get_player(uid, game_config["season_id"])
            if player:
                rep_text = f" | Rep: {player['reputation_score']}"

        embed.add_field(
            name=f"{medal} {name}",
            value=f"💰 ${money:,.0f}{rep_text}",
            inline=False
        )

    await channel.send(embed=embed)


# ========== REPUTATION COMMANDS ==========
@bot.tree.command(name="reputation", description="Check your or another player's reputation")
@app_commands.describe(user="User to check (leave blank for yourself)")
async def reputation(interaction: discord.Interaction, user: discord.Member = None):
    """Check reputation"""
    if not game_config["season_active"]:
        await interaction.response.send_message("❌ No active season!", ephemeral=True)
        return

    target_user = user or interaction.user

    player_data = db.get_player(target_user.id, game_config["season_id"])

    if not player_data:
        await interaction.response.send_message(
            f"❌ {target_user.display_name} hasn't participated in this season yet!",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"⭐ Reputation - {target_user.display_name}",
        color=discord.Color.blue()
    )

    rep_score = player_data['reputation_score']

    # Determine reputation tier
    if rep_score >= 150:
        tier = "🌟 Legendary"
        color = discord.Color.gold()
    elif rep_score >= 120:
        tier = "✨ Excellent"
        color = discord.Color.green()
    elif rep_score >= 100:
        tier = "👍 Good"
        color = discord.Color.blue()
    elif rep_score >= 80:
        tier = "⚠️ Fair"
        color = discord.Color.orange()
    else:
        tier = "❌ Poor"
        color = discord.Color.red()

    embed.color = color
    embed.add_field(name="Reputation Score", value=f"{rep_score}/200", inline=True)
    embed.add_field(name="Tier", value=tier, inline=True)

    # Get recent reputation events
    events = db.get_reputation_history(target_user.id, game_config["season_id"])

    if events:
        recent_events = events[:5]  # Show last 5 events
        event_text = "\n".join([
            f"{'➕' if e['change_amount'] > 0 else '➖'} {e['change_amount']:+d}: {e['reason']}"
            for e in recent_events
        ])
        embed.add_field(name="Recent Events", value=event_text, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== IPO COMMANDS ==========
@bot.tree.command(name="ipo_suggest_terms", description="[ADMIN] Get suggested IPO terms for a business")
@app_commands.describe(business_id="The business ID")
@app_commands.checks.has_permissions(administrator=True)
async def ipo_suggest_terms(interaction: discord.Interaction, business_id: str):
    """Get suggested IPO terms"""
    if business_id not in businesses:
        await interaction.response.send_message("❌ Business not found!", ephemeral=True)
        return

    biz = businesses[business_id]

    terms = ipo_system.calculate_ipo_terms(
        biz['valuation'],
        biz['equity_given'],
        biz['initial_quality'],
        biz['final_quality']
    )

    embed = discord.Embed(
        title=f"📊 Suggested IPO Terms - {biz['entrepreneur_name']}'s Business",
        description=biz['pitch'][:100] + "...",
        color=discord.Color.blue()
    )

    embed.add_field(name="Suggested Share Price", value=f"${terms['suggested_share_price']}", inline=True)
    embed.add_field(name="Total Shares", value=f"{terms['total_shares']:,}", inline=True)
    embed.add_field(name="Shares to Offer", value=f"{terms['shares_to_offer']:,} ({terms['ipo_percentage']}%)",
                    inline=True)
    embed.add_field(name="Expected Raise", value=f"${terms['expected_raise']:,}", inline=True)
    embed.add_field(name="Post-IPO Valuation", value=f"${terms['post_ipo_valuation']:,}", inline=True)
    embed.add_field(name="Quality Score", value=f"{terms['quality_score']}/10", inline=True)

    embed.set_footer(text="Use /ipo_start with these suggested values or customize as needed")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="ipo_start", description="[ADMIN] Start an IPO for a business")
@app_commands.describe(
    business_id="The business ID",
    share_price="Price per share",
    shares_to_offer="Number of shares to offer",
    duration_hours="How long the IPO lasts (hours)"
)
@app_commands.checks.has_permissions(administrator=True)
async def ipo_start(
        interaction: discord.Interaction,
        business_id: str,
        share_price: float,
        shares_to_offer: int,
        duration_hours: int = 24
):
    """Start an IPO"""
    if business_id not in businesses:
        await interaction.response.send_message("❌ Business not found!", ephemeral=True)
        return

    # Check if IPO already exists
    existing_ipo = ipo_system.get_active_ipo_for_business(business_id)
    if existing_ipo:
        await interaction.response.send_message("❌ This business already has an active IPO!", ephemeral=True)
        return

    biz = businesses[business_id]

    # Create IPO
    total_shares = shares_to_offer * 4  # Offering 25% of total
    ipo_id = ipo_system.create_ipo(
        business_id,
        game_config["season_id"],
        share_price,
        total_shares,
        shares_to_offer,
        duration_hours
    )

    embed = discord.Embed(
        title="📈 IPO LAUNCHED!",
        description=f"**{biz['entrepreneur_name']}'s Business** is now public!",
        color=discord.Color.green()
    )

    embed.add_field(name="Business", value=biz['pitch'][:100] + "...", inline=False)
    embed.add_field(name="💵 Share Price", value=f"${share_price}", inline=True)
    embed.add_field(name="📊 Shares Available", value=f"{shares_to_offer:,}", inline=True)
    embed.add_field(name="⏰ Duration", value=f"{duration_hours} hours", inline=True)
    embed.add_field(name="💰 Total Raise Potential", value=f"${share_price * shares_to_offer:,}", inline=True)
    embed.add_field(name="🆔 IPO ID", value=f"#{ipo_id}", inline=True)

    embed.set_footer(text="Use /ipo_buy to purchase shares!")

    await interaction.response.send_message(embed=embed)

    # Log event
    await log_event(interaction.guild, "IPO Started",
                    f"IPO #{ipo_id} for {biz['entrepreneur_name']}'s business is now live!", embed)


@bot.tree.command(name="ipo_buy", description="Buy shares in an IPO")
@app_commands.describe(
    ipo_id="The IPO ID",
    shares="Number of shares to buy",
    order_type="Market (buy now) or Limit (buy at specific price)",
    limit_price="If using limit order, max price per share"
)
async def ipo_buy(
        interaction: discord.Interaction,
        ipo_id: int,
        shares: int,
        order_type: str = "market",
        limit_price: float = None
):
    """Buy IPO shares"""
    if not game_config["season_active"]:
        await interaction.response.send_message("❌ No active season!", ephemeral=True)
        return

    ensure_player_money(interaction.user.id, is_shark=has_role(interaction.user, SHARK_ROLE_ID))

    user_balance = player_money.get(interaction.user.id, 0)

    ipo = ipo_system.get_ipo(ipo_id)
    if not ipo:
        await interaction.response.send_message("❌ IPO not found!", ephemeral=True)
        return

    # Estimate cost
    estimated_cost = shares * ipo['share_price']

    if user_balance < estimated_cost:
        await interaction.response.send_message(
            f"❌ Insufficient funds! You have ${user_balance:,} but need ~${estimated_cost:,}",
            ephemeral=True
        )
        return

    # Place order
    if order_type.lower() == "market":
        success, message, order_id = ipo_system.place_market_order(
            ipo_id,
            interaction.user.id,
            interaction.user.display_name,
            shares
        )
    else:
        if limit_price is None:
            await interaction.response.send_message("❌ Limit price required for limit orders!", ephemeral=True)
            return

        success, message, order_id = ipo_system.place_limit_order(
            ipo_id,
            interaction.user.id,
            interaction.user.display_name,
            shares,
            limit_price
        )

    if success:
        # Deduct money if order was filled
        if "filled" in message.lower():
            player_money[interaction.user.id] -= estimated_cost
            if game_config["season_id"]:
                db.update_player_balance(interaction.user.id, game_config["season_id"],
                                         player_money[interaction.user.id])

        embed = discord.Embed(
            title="✅ IPO Order Placed",
            description=message,
            color=discord.Color.green()
        )
        embed.add_field(name="Order ID", value=f"#{order_id}", inline=True)
        embed.add_field(name="New Balance", value=f"${player_money[interaction.user.id]:,}", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log event
        await log_event(interaction.guild, "IPO Purchase",
                        f"{interaction.user.display_name} bought {shares} shares in IPO #{ipo_id}")
    else:
        await interaction.response.send_message(f"❌ {message}", ephemeral=True)


@bot.tree.command(name="ipo_close", description="[ADMIN] Close an IPO early")
@app_commands.describe(ipo_id="The IPO ID to close")
@app_commands.checks.has_permissions(administrator=True)
async def ipo_close(interaction: discord.Interaction, ipo_id: int):
    """Close IPO"""
    success, message, summary = ipo_system.close_ipo(ipo_id)

    if success:
        embed = discord.Embed(
            title="🔒 IPO CLOSED",
            description=f"IPO #{ipo_id} has been closed",
            color=discord.Color.blue()
        )

        embed.add_field(name="Total Orders", value=str(summary['total_orders']), inline=True)
        embed.add_field(name="Shares Sold", value=f"{summary['total_shares_sold']:,}", inline=True)
        embed.add_field(name="Total Raised", value=f"${summary['total_raised']:,}", inline=True)
        embed.add_field(name="Unique Investors", value=str(summary['unique_investors']), inline=True)
        embed.add_field(name="Shares Remaining", value=f"{summary['shares_remaining']:,}", inline=True)

        await interaction.response.send_message(embed=embed)

        # Log event
        await log_event(interaction.guild, "IPO Closed", f"IPO #{ipo_id} closed - Raised ${summary['total_raised']:,}",
                        embed)
    else:
        await interaction.response.send_message(f"❌ {message}", ephemeral=True)


@bot.tree.command(name="ipo_list", description="View all active IPOs")
async def ipo_list(interaction: discord.Interaction):
    """List active IPOs"""
    if not game_config["season_active"]:
        await interaction.response.send_message("❌ No active season!", ephemeral=True)
        return

    active_ipos = ipo_system.get_all_active_ipos(game_config["season_id"])

    if not active_ipos:
        await interaction.response.send_message("📊 No active IPOs at the moment.")
        return

    embed = discord.Embed(
        title="📈 Active IPOs",
        description="Current public offerings available for investment",
        color=discord.Color.blue()
    )

    for ipo in active_ipos:
        biz_id = ipo['business_id']
        biz = businesses.get(biz_id)

        if biz:
            summary = ipo_system.get_ipo_summary(ipo['ipo_id'])

            time_left = datetime.fromisoformat(ipo['end_time']) - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)

            field_value = (
                f"**Share Price:** ${ipo['share_price']}\n"
                f"**Available:** {summary['shares_available']:,}/{summary['total_shares']:,} shares\n"
                f"**Raised:** ${summary['total_raised']:,}\n"
                f"**Time Left:** {hours_left}h\n"
                f"**IPO ID:** #{ipo['ipo_id']}"
            )

            embed.add_field(
                name=f"🏢 {biz['entrepreneur_name']}'s Business",
                value=field_value,
                inline=False
            )

    embed.set_footer(text="Use /ipo_buy <ipo_id> <shares> to invest!")

    await interaction.response.send_message(embed=embed)


# ========== CONTINUE WITH ORIGINAL COMMANDS ==========
# (All player commands from original bot)

@bot.tree.command(name="balance", description="Check your current balance")
async def balance(interaction: discord.Interaction):
    """Check balance"""
    if interaction.user.id not in player_money:
        await interaction.response.send_message("❌ You haven't participated in any deals yet!", ephemeral=True)
        return

    balance_amt = player_money[interaction.user.id]

    embed = discord.Embed(title="💰 Your Balance", color=discord.Color.green())
    embed.add_field(name="Current Money", value=f"${balance_amt:,}")

    # Show businesses if entrepreneur
    user_businesses = [b for b in businesses.values() if b["entrepreneur_id"] == interaction.user.id]
    if user_businesses:
        biz_text = "\n".join([f"• {b['pitch'][:40]}..." for b in user_businesses])
        embed.add_field(name="Your Businesses", value=biz_text, inline=False)

    # Show reputation if available
    if game_config["season_id"]:
        player_data = db.get_player(interaction.user.id, game_config["season_id"])
        if player_data:
            embed.add_field(name="Reputation", value=f"⭐ {player_data['reputation_score']}/200", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


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

        # Get reputation
        rep_text = ""
        if game_config["season_id"]:
            player = db.get_player(uid, game_config["season_id"])
            if player:
                rep_text = f" | Rep: {player['reputation_score']}"

        embed.add_field(
            name=f"{medal} {name}",
            value=f"💰 ${money:,}{rep_text}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pitch", description="Pitch your business idea to the Sharks")
@app_commands.describe(
    idea="Describe your business idea",
    asking_amount="Amount of money you're asking for",
    asking_equity="Equity percentage you're offering"
)
async def slash_pitch(interaction: discord.Interaction, idea: str, asking_amount: int, asking_equity: float):
    """Entrepreneur pitches their idea"""
    if not SHARK_ROLE_ID or not ENTREPRENEUR_ROLE_ID:
        await interaction.response.send_message(
            "❌ Game not configured! An admin must run `/admin_set_roles` first.",
            ephemeral=True
        )
        return

    if not has_role(interaction.user, ENTREPRENEUR_ROLE_ID):
        await interaction.response.send_message("❌ Only users with the **Entrepreneur** role can pitch.",
                                                ephemeral=True)
        return

    if interaction.user.id in eliminated_entrepreneurs:
        await interaction.response.send_message("❌ You have been eliminated from this season. Better luck next time!",
                                                ephemeral=True)
        return

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

    # Generate random business quality score
    business_quality = random.randint(game_config["quality_range_min"], game_config["quality_range_max"])
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

    # Log event
    await log_event(interaction.guild, "New Pitch",
                    f"{interaction.user.display_name} is pitching for ${asking_amount:,}", embed)


# ========== SHARK OFFER SYSTEM (from original) ==========
class SharkOfferView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction):
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


# [Continue with all other original classes and functions...]
# I'll include the remaining essential parts

class SoloOfferModal(discord.ui.Modal, title="💰 Shark Offer"):
    amount = discord.ui.TextInput(label="Investment Amount", placeholder="e.g., 100000")
    equity = discord.ui.TextInput(label="Equity %", placeholder="e.g., 25")
    conditions = discord.ui.TextInput(
        label="Conditions (Optional)",
        required=False,
        placeholder="e.g., Must hire CFO",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        amount_val = float(self.amount.value.replace("$", "").replace(",", ""))
        equity_val = float(self.equity.value.replace("%", ""))

        if player_money.get(interaction.user.id, 0) < amount_val:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have ${player_money.get(interaction.user.id, 0):,}",
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


async def print_offer(channel, offer_id):
    offer = round_data["offers"][offer_id]
    valuation = (offer["amount"] / offer["equity"]) * 100

    embed = discord.Embed(title="💼 SHARK OFFER", color=discord.Color.green())
    embed.add_field(name="🦈 Sharks", value=", ".join(offer["shark_names"]), inline=False)
    embed.add_field(name="💰 Amount", value=f"${offer['amount']:,}", inline=True)
    embed.add_field(name="📊 Equity", value=f"{offer['equity']}%", inline=True)
    embed.add_field(name="💎 Valuation", value=f"${valuation:,.0f}", inline=True)
    embed.add_field(name="📜 Conditions", value=offer["conditions"], inline=False)

    await channel.send(embed=embed, view=EntrepreneurDecisionView(offer_id))


class EntrepreneurDecisionView(discord.ui.View):
    def __init__(self, offer_id):
        super().__init__(timeout=None)
        self.offer_id = offer_id

    async def interaction_check(self, interaction):
        if interaction.user.id != round_data["entrepreneur_id"]:
            await interaction.response.send_message("❌ Only the entrepreneur can respond.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Accept Deal", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        offer = round_data["offers"][self.offer_id]

        # Deduct from sharks
        amount_per_shark = offer["amount"] / len(offer["sharks"])
        for sid in offer["sharks"]:
            player_money[sid] -= amount_per_shark

        # Give to entrepreneur
        if interaction.user.id not in player_money:
            player_money[interaction.user.id] = 0
        player_money[interaction.user.id] += offer["amount"]

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

        # Save to database
        if game_config["season_id"]:
            db.create_business(
                round_data["business_id"],
                game_config["season_id"],
                interaction.user.id,
                interaction.user.display_name,
                round_data["pitch"],
                round_data["asking_amount"],
                round_data["asking_equity"],
                round_data["business_quality"],
                valuation,
                businesses[round_data["business_id"]]["deadline"]
            )

            for sid in offer["sharks"]:
                db.add_investment(
                    round_data["business_id"],
                    sid,
                    interaction.guild.get_member(sid).display_name,
                    amount_per_shark,
                    offer["equity"] / len(offer["sharks"]),
                    offer["conditions"]
                )

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        round_data["active"] = False

        embed = discord.Embed(
            title="🎉 DEAL CLOSED!",
            description=f"**{round_data['entrepreneur_name']}** accepted!",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

        # Log event
        await log_event(interaction.guild, "Deal Closed",
                        f"{interaction.user.display_name} accepted ${offer['amount']:,} for {offer['equity']}%")

        try:
            await send_investment_dm(interaction.user, round_data["business_id"])
        except:
            await interaction.channel.send(f"⚠️ {interaction.user.mention} - Enable DMs!")


async def send_investment_dm(user, business_id):
    """Send investment options via DM"""
    business = businesses[business_id]
    capital = business["investment"]

    embed = discord.Embed(
        title="💰 INVESTMENT PHASE",
        description=f"You have **${capital:,}** to invest!",
        color=discord.Color.gold()
    )

    await user.send(embed=embed)


@bot.tree.command(name="invest", description="Invest your capital")
@app_commands.describe(option="1 (Basic), 2 (Moderate), or 3 (Aggressive)")
async def invest_command(interaction: discord.Interaction, option: int):
    """Invest capital"""
    user_business = None

    for bid, biz in businesses.items():
        if biz["entrepreneur_id"] == interaction.user.id and not biz["investment_complete"]:
            user_business = biz
            business_id = bid
            break

    if not user_business:
        await interaction.response.send_message("❌ No active business!", ephemeral=True)
        return

    if option not in [1, 2, 3]:
        await interaction.response.send_message("❌ Invalid option!", ephemeral=True)
        return

    tier = INVESTMENT_TIERS[str(option)]
    available = user_business["investment"] - user_business["capital_invested"]

    if available < tier["cost"]:
        await interaction.response.send_message(f"❌ Insufficient capital!", ephemeral=True)
        return

    user_business["capital_invested"] += tier["cost"]
    user_business["quality_boost"] += tier["quality_boost"]
    user_business["final_quality"] = user_business["initial_quality"] + user_business["quality_boost"]

    # Update database
    if game_config["season_id"]:
        db.update_business_investment(
            business_id,
            user_business["capital_invested"],
            user_business["quality_boost"],
            user_business["final_quality"],
            False
        )

    await interaction.response.send_message(f"✅ Invested in {tier['name']}!", ephemeral=True)

    # Log event
    await log_event(interaction.guild, "Investment Made", f"{interaction.user.display_name} invested ${tier['cost']:,}")


@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")

        # Start background tasks
        check_ipo_expirations.start()

        print(f"\n{'=' * 50}")
        print(f"🦈 SHARK TANK BOT READY!")
        print(f"{'=' * 50}\n")
    except Exception as e:
        print(f"❌ Error: {e}")


bot.run(TOKEN)