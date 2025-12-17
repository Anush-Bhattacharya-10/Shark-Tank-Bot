# 🦈 Shark Tank Discord Bot

<p align="center">
  <strong>An interactive Shark Tank–style negotiation & investment game for Discord servers</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Discord" src="https://img.shields.io/badge/Discord.py-2.x-purple">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/Status-Stable-brightgreen">
</p>

---

## 📌 Overview

**Shark Tank Discord Bot** is a fully interactive Discord game inspired by the *Shark Tank* TV format. Entrepreneurs pitch ideas, Sharks negotiate deals (solo or joint), capital is invested strategically via DM, and businesses are evaluated at the end of a season to determine the richest player.

The bot is built entirely on **Discord Slash Commands, Buttons, Modals, Select Menus, and DM interactions**, requiring no manual tracking by admins once configured.

**Winner = Richest person (Shark OR Entrepreneur) at season's end!** 🏆

<p align="center"> <a href="https://discord.com/oauth2/authorize?client_id=1450522916986028072&permissions=2416003072&integration_type=0&scope=bot+applications.commands"> Add to your servers now! </a></p>

---

## ✨ Feature Highlights

### 🎤 Pitch & Negotiation System

* **One pitch per entrepreneur per season** (no second chances!)
* Real-time negotiation using interactive buttons and modals
* **Endless negotiation rounds** - no limit on back-and-forth offers
* Sharks can:
  * Make solo offers with custom terms
  * Form **joint offers with multi-shark consent system**
  * Counter-offer, accept entrepreneur counters, or decline
  * Declare "I'm Out" publicly
* Entrepreneurs can:
  * Accept or reject any offer
  * **Counter-offer** with new terms
  * Walk away (results in **elimination** from season)

### 🤝 Joint Offer Consent System

* Initiating shark selects partners via dropdown menu
* **All selected sharks must approve** before offer becomes active
* Initiator auto-approves; others vote via buttons
* Any shark declining cancels the entire joint offer
* Prevents unwanted partnerships

### 💰 Post-Deal Investment Phase (DM-Based)

After accepting a deal, entrepreneurs receive investment capital and enter the **secret investment phase**:

* Investment options sent via **private DM**
* **Three investment tiers:**
  * **Basic Growth** ($25,000) → +1 Quality Score
  * **Moderate Expansion** ($75,000) → +3 Quality Score
  * **Aggressive Scale** ($150,000) → +5 Quality Score
* **Multiple investments allowed** until capital is exhausted
* Remaining capital automatically added to balance
* 48-hour deadline (configurable by admin)
* Commands: `/invest <1|2|3>` and `/finish_investing`

### 📊 Business Simulation Engine

* Each business receives a **hidden quality score (1–10)** at pitch time
* Quality score determines:
  * **Success probability** (10% per point, max 100%)
  * **Valuation multiplier** on success (1.5x to 5x based on final quality)
* Final quality = Initial quality + Investment boosts
* **Outcome calculation:**
  * ✅ **Success:** Business valuation grows exponentially
  * ❌ **Failure:** Business worth $0
* Automatic **profit distribution:**
  * Entrepreneur receives payout based on retained equity %
  * Sharks receive payout split based on their equity %

### 🏆 Seasons & Winner Determination

* Admin-controlled season lifecycle
* **Shared economy:** Sharks AND Entrepreneurs compete for wealth
* Live money leaderboard (`/leaderboard`)
* End-of-season business report (`/admin_business_report`) reveals:
  * Business success/failure outcomes
  * Quality scores and investment details
  * Final payouts to all parties
* **Winner = Richest player overall** (can be shark OR entrepreneur!)

### 🎮 Elimination Rules

* Entrepreneurs who **walk away** are **permanently eliminated**
* Eliminated players cannot pitch again in that season
* Creates high-stakes decision making

---

## 🧑‍💼 Required Discord Roles

Roles are **configured in Discord** by admins using `/admin_set_roles`:

| Role             | Abilities                           |
| ---------------- | ----------------------------------- |
| **Shark**        | Make offers, negotiate, invest money|
| **Entrepreneur** | Pitch businesses once per season    |
| **Admin**        | Manage seasons, economy, and config |

**No hardcoded role IDs** - all roles set dynamically via commands.

---

## 📂 Project Structure

```text
Shark-Tank-Bot/
├── Shark-Tank.py        # Main bot logic with all game mechanics
├── start.bat           # Windows: Start bot
├── stop.bat            # Windows: Stop bot
├── .env                # Environment variables (gitignored)
├── requirements.txt    # Python dependencies
├── .venv/              # Virtual environment (gitignored)
└── README.md           # This file
```

---

## ⚙️ Setup & Installation

### 1️⃣ Prerequisites

* **Python 3.10+** installed
* **Discord Bot** created at [Discord Developer Portal](https://discord.com/developers/applications)
* Bot invited with `applications.commands` and `bot` scopes
* Required **Privileged Gateway Intents** enabled:
  * Message Content Intent
  * Server Members Intent

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/Anush-Bhattacharya-10/Shark-Tank-Bot.git
cd Shark-Tank-Bot
```

### 3️⃣ Create & Activate Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
* `discord.py>=2.0`
* `python-dotenv`

### 5️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

**⚠️ Security:** Never commit `.env` to Git. It's already in `.gitignore`.

---

## ▶️ Running the Bot

### ✅ Start (Bring Bot Online)

**Windows:**
```bash
start.bat
```

**macOS/Linux:**
```bash
python Shark-Tank.py
```

Console output will confirm:
```
✅ BotName is online!
Shark Role ID: Not set - use /admin_set_roles
Entrepreneur Role ID: Not set - use /admin_set_roles
✅ Synced 20 slash command(s)

==================================================
🦈 SHARK TANK BOT READY!
==================================================
⚠️  SETUP REQUIRED: Run /admin_set_roles in Discord
==================================================
```

### ⛔ Stop (Take Bot Offline)

**Windows:**
```bash
stop.bat
```

**macOS/Linux:**
```bash
# Press Ctrl+C in terminal
```

---

## 🎯 First-Time Setup in Discord

### Step 1: Create Roles
In your Discord server, create two roles:
* `Shark`
* `Entrepreneur`

### Step 2: Configure Bot Roles
Run this command in any channel:
```
/admin_set_roles shark_role:@Shark entrepreneur_role:@Entrepreneur
```

### Step 3: Start Season
```
/admin_start_season
```

### Step 4: Assign Roles
Assign the Shark/Entrepreneur roles to your players.

### Step 5: Let Players Learn
Players can run `/help` to see the complete game guide!

---

## 🧾 Command Reference

### 📘 Help & Information

| Command | Description |
|---------|-------------|
| `/help` | Comprehensive game guide (personalized by role) |
| `/balance` | Check your current money balance |
| `/leaderboard` | View richest players |
| `/status` | Check if there's an active pitch |

### 👔 Entrepreneur Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/pitch` | Pitch your business idea | `/pitch idea:"AI Chatbot" asking_amount:100000 asking_equity:20` |
| `/invest` | Invest capital to boost quality | `/invest option:2` |
| `/finish_investing` | End investment phase early | `/finish_investing` |

**During Negotiation (Buttons):**
* ✅ Accept Deal
* ❌ Decline Offer
* 💬 Counter Offer
* 🛑 Walk Away (eliminates you!)

### 🦈 Shark Commands

**During Pitches (Buttons):**
* 💰 Make Offer (solo)
* 🤝 Joint Offer (partner with other sharks)
* 🚫 I'm Out

**During Negotiation:**
* Accept entrepreneur counters
* Make new offers
* Counter back

### ⚙️ Admin Commands

#### Season Management
| Command | Description |
|---------|-------------|
| `/admin_set_roles` | **REQUIRED FIRST** - Configure Shark & Entrepreneur roles |
| `/admin_start_season` | Start new season (resets all data) |
| `/admin_end_season` | End current season |
| `/admin_business_report` | Calculate business outcomes & determine winners |

#### Configuration
| Command | Description |
|---------|-------------|
| `/admin_config` | View all current settings |
| `/admin_set_shark_money` | Set starting money for sharks (default: $1M) |
| `/admin_set_deadline` | Set investment deadline in hours (default: 48) |

#### Economy Management
| Command | Description |
|---------|-------------|
| `/admin_give_money` | Give money to a player |
| `/admin_set_balance` | Set exact balance for a player |
| `/admin_view_businesses` | See all businesses with quality scores |

---

## 🎮 How to Play

### Game Flow Overview

```
1. Admin starts season → All balances reset
2. Entrepreneur pitches (one per season)
3. Sharks negotiate and make offers
4. Entrepreneur accepts OR walks away (eliminated)
5. Entrepreneur invests capital via DM (secret)
6. Repeat for all entrepreneurs
7. Admin runs business report
8. Winner announced (richest player)
```

### For Entrepreneurs 👔

1. **Prepare your pitch:**
   * Business idea description
   * Amount of money needed
   * Equity percentage you're offering
   
2. **Pitch using `/pitch`:**
   ```
   /pitch idea:"Mobile Food Delivery App" asking_amount:150000 asking_equity:15
   ```
   This asks for $150K in exchange for 15% equity (implying $1M valuation)

3. **Negotiate with Sharks:**
   * Review offers carefully
   * Counter-offer to improve terms
   * Accept best deal OR walk away
   * ⚠️ Walking away eliminates you!

4. **Invest Capital (via DM):**
   * Bot sends investment options
   * Choose wisely based on available capital
   * Higher quality = better success chance
   * Leftover money goes to your balance

5. **Wait for Business Report:**
   * Admin calculates outcomes
   * Successful businesses pay you based on retained equity
   * Failed businesses pay nothing

### For Sharks 🦈

1. **Listen to pitches** and evaluate ideas

2. **Make strategic offers:**
   * Solo investment for full equity
   * Joint investment to share risk
   * Consider valuation carefully

3. **Negotiate endlessly:**
   * Counter entrepreneur offers
   * Accept their counters
   * Walk away if deal is bad

4. **Watch your budget:**
   * You have $1M starting capital (default)
   * Don't overcommit to bad deals
   * Diversify investments

5. **Wait for outcomes:**
   * Successful businesses pay you based on your equity
   * Failed businesses lose your investment

### Pro Tips 💡

* **Entrepreneurs:** Keep as much equity as possible while still getting capital
* **Sharks:** Quality scores are hidden - judge pitches carefully
* **Both:** Success isn't guaranteed - even great businesses can fail!
* **Strategy:** Balanced portfolio beats all-or-nothing bets

---

## 🎲 Investment Tiers Explained

After closing a deal, entrepreneurs choose how to invest:

| Tier | Cost | Quality Boost | Best For |
|------|------|---------------|----------|
| **Basic Growth** | $25K | +1 | Small improvements, conserving capital |
| **Moderate Expansion** | $75K | +3 | Balanced risk/reward |
| **Aggressive Scale** | $150K | +5 | Maximum growth, high investment |

**Example Strategy:**
* Received $200K investment
* Buy 1x Aggressive Scale ($150K) → +5 quality
* Buy 2x Basic Growth ($50K) → +2 quality
* Total: $200K spent, +7 quality boost
* Leftover: $0

**OR:**
* Buy 2x Moderate Expansion ($150K) → +6 quality
* Leftover: $50K (goes to your balance)

---

## 📊 Business Success Mechanics

### Quality Score System

```
Initial Quality (Hidden): 1-10 (randomly assigned)
Investment Boosts: +0 to +15 (from entrepreneur spending)
Final Quality: Initial + Boosts

Success Chance = Final Quality × 10%
(Max 100% at quality 10+)

If Success:
  Valuation Multiplier = 1.5x to 5x (based on final quality)
  Final Valuation = Initial Valuation × Multiplier
  
If Failure:
  Final Valuation = $0
```

### Payout Distribution

**Example:**
* Deal: $200K for 25% equity (implying $800K valuation)
* Final quality: 8/10
* Outcome: Success! Multiplier 3.3x
* Final valuation: $800K × 3.3 = $2.64M

**Payouts:**
* Shark (25% equity): $660K
* Entrepreneur (75% equity): $1.98M
* Both profit from success! 🎉

---

## 🔐 Security & Best Practices

* `.env` is excluded from Git by default (`.gitignore`)
* **Never commit your Discord bot token**
* Restrict Admin commands to trusted server administrators
* DM-based investments keep strategies secret
* No persistent database = season data resets on bot restart

---

## 🧠 Design Philosophy

* **Event-driven:** Fully automated gameplay, minimal admin intervention
* **Strategic depth:** Hidden variables, risk management, negotiation skills
* **High stakes:** Elimination mechanic creates tension
* **Fair competition:** Sharks and Entrepreneurs compete equally
* **Replayable:** Seasonal structure with fresh starts

---

## 🛠️ Technical Details

* **Framework:** Discord.py 2.x
* **Architecture:** Event-driven with slash commands
* **State Management:** In-memory (resets on restart)
* **UI Components:** Buttons, Modals, Select Menus, Embeds
* **DM System:** Private investment phase via direct messages
* **No Database:** Intentionally ephemeral for season-based play

---

## 🚧 Known Limitations

* **No persistence:** Data lost on bot restart (restart mid-season = reset)
* **Single server:** Bot state shared across all servers (run separate instances for multiple servers)
* **No undo:** Accepted deals cannot be reversed
* **Investment deadline:** Entrepreneurs who miss deadline cannot invest (business stays at base quality)

---

## 🔮 Future Enhancement Ideas

* IPO for companies after after funding (in development!!)
* Persistent database (SQLite/PostgreSQL) (in development!!)
* Web dashboard for stats (in development!!)
* Advisor roles with special abilities
* Business milestone events
* Shark power-ups (steal deals, veto, etc.)
* Achievements and badges
* Historical season leaderboards

---

## 📜 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Anush Bhattacharya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Please ensure:**
* Code follows existing style
* Commands are documented
* New features are explained in README updates

---

## 🙏 Acknowledgments

* Inspired by the *Shark Tank* TV show format
* Built with [Discord.py](https://discordpy.readthedocs.io/)
* Community feedback and testing

---

## 📞 Support

* **Issues:** [GitHub Issues](https://github.com/Anush-Bhattacharya-10/Shark-Tank-Bot/issues)
* **Discussions:** Use GitHub Discussions for questions
* **Discord Support:** Use `/help` command in-bot

---

<p align="center">
  <strong>Built for Discord communities that enjoy strategy, negotiation, and controlled chaos in the tank.</strong> 🦈💰
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Anush-Bhattacharya-10">Anush Bhattacharya</a> (Claude I love you too)
</p>
