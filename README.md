# 🦈 Shark Tank Discord Bot

<p align="center">
  <strong>An interactive Shark Tank–style negotiation & investment game for Discord servers</strong><br>
  <em>Now with Persistent Database, IPO System, Reputation Tracking & More!</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Discord" src="https://img.shields.io/badge/Discord.py-2.x-purple">
  <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-orange">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/Status-Ready-brightgreen">
</p>

---

## 📌 Overview

**Shark Tank Discord Bot** is a fully interactive Discord game inspired by the *Shark Tank* TV format. Entrepreneurs pitch ideas, Sharks negotiate deals (solo or joint), capital is invested strategically via DM, businesses are evaluated at season's end, and now you can **take companies public with IPOs**!

Built on **Discord Slash Commands, Buttons, Modals, and a persistent SQLite database** - no manual tracking needed once configured.

**Winner = Richest person (Shark OR Entrepreneur) at season's end!** 🏆

<p align="center"> 
  <a href="https://discord.com/oauth2/authorize?client_id=1450522916986028072&permissions=2416003072&integration_type=0&scope=bot+applications.commands"> 
    <strong>Add to your servers now!</strong>
  </a>
</p>

---

## 🆕 What's New in V1.2.0

### 🗄️ **Persistent Database System**
- SQLite database stores all game data
- Survives bot restarts - no data loss!
- Complete history tracking for analytics
- Season, player, business, and IPO records

### 📈 **IPO System** 
- Take successful businesses public!
- AI-calculated suggested share prices
- Market orders (instant buy) and limit orders (price target)
- Configurable IPO duration
- Auto-closes when time expires
- Detailed IPO summaries and analytics

### 📢 **Event Logging**
- Automatic notifications for:
  - New pitches and deals
  - Investment activity
  - IPO launches and closures
  - Business reports
  - Player penalties
  - Leaderboard updates

### ⚙️ **Advanced Admin Controls**
- Season configuration wizard
- Private business quality viewing
- Player penalty system (money + reputation)
- Quality range reveal command
- Configurable quality ranges
- Flexible starting balances

### 🏗️ **Modular Architecture**
- Clean, maintainable codebase
- Easy to extend with new features

---

## ✨ Core Feature Highlights

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
  * **Basic Growth** ($10,000) → +1 Quality Score
  * **Moderate Expansion** ($75,000) → +3 Quality Score
  * **Aggressive Scale** ($150,000) → +5 Quality Score
* **Multiple investments allowed** until capital is exhausted
* Remaining capital automatically added to balance
* Configurable deadline (default: 48 hours)
* Commands: `/invest <1|2|3>` and `/finish_investing`

### 📊 Business Simulation Engine

* Each business receives a **hidden quality score** at pitch time
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

### 📈 IPO System (NEW!)

* **AI-Suggested Terms:** Get calculated share price and allocation
* **Market Orders:** Buy shares instantly at current price
* **Limit Orders:** Set price targets and wait for execution
* **Configurable Duration:** Admin sets IPO open time (hours)
* **Auto-Close:** IPOs automatically close when time expires
* **Investor Tracking:** Complete order history and analytics
* **Capital Raise:** Entrepreneurs get IPO proceeds
* **Diversification:** Players can invest in multiple businesses

### 🏆 Seasons & Winner Determination

* Admin-controlled season lifecycle
* **Shared economy:** Sharks AND Entrepreneurs compete for wealth
* Live money leaderboard (`/leaderboard`) with reputation scores
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
├── shark_tank.db        # SQLite database (auto-created)
├── start.bat            # Windows: Start bot
├── stop.bat             # Windows: Stop bot
├── .env                 # Environment variables (gitignored)
├── requirements.txt     # Python dependencies
├── .venv/               # Virtual environment (gitignored)
└── README.md            # This file
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

**Note:** SQLite is built into Python - no extra installation needed!

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
Note: Make sure venv is activated

**Linux:**
```bash
./start.sh
```
Note: Venv gets activated using this script, so that step can be skipped.

Console output will confirm:
```
✅ Shark Tank Bot is online!
✅ Synced 19 slash command(s)
✅ Database initialized successfully

==================================================
🦈 SHARK TANK BOT READY!
==================================================
⚠️  SETUP REQUIRED: Run /admin_set_roles in Discord
==================================================
```

The database (`shark_tank.db`) will be automatically created on first run!

### ⛔ Stop (Take Bot Offline)

**Windows:**
```bash
stop.bat
```

**Linux:**
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

### Step 3: Set Event Channel (Recommended)
```
/admin_set_event_channel channel:#shark-tank-events
```

### Step 4: Configure Season Settings (Optional)
```
/admin_configure_season shark_money:1000000 entrepreneur_money:0 investment_deadline:48 quality_min:1 quality_max:10
```

### Step 5: Start Season
```
/admin_start_season
```

### Step 6: Assign Roles
Assign the Shark/Entrepreneur roles to your players.

### Step 7: Let Players Learn
Players can run `/help` to see the complete game guide!

---

## 🧾 Command Reference

### 📘 Help & Information

| Command | Description |
|---------|-------------|
| `/help` | Comprehensive game guide (personalized by role) |
| `/balance` | Check your money balance and reputation |
| `/leaderboard` | View richest players with reputation scores |
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

### 📈 IPO Commands (All Players)

| Command | Description | Example |
|---------|-------------|---------|
| `/ipo_list` | View all active IPOs | `/ipo_list` |
| `/ipo_buy` | Buy shares in an IPO | `/ipo_buy ipo_id:1 shares:100 order_type:market` |

**Order Types:**
* **Market Order:** Buy immediately at current price (guaranteed fill)
* **Limit Order:** Set maximum price, order fills if price matches

### ⚙️ Admin Commands

#### Season Management
| Command | Description |
|---------|-------------|
| `/admin_set_roles` | **REQUIRED FIRST** - Configure Shark & Entrepreneur roles |
| `/admin_set_event_channel` | Set channel for automatic event logging |
| `/admin_configure_season` | Configure season settings before starting |
| `/admin_start_season` | Start new season with configured settings |
| `/admin_end_season` | End current season |
| `/admin_business_report` | Calculate business outcomes & determine winners |

#### Configuration & Viewing
| Command | Description |
|---------|-------------|
| `/admin_config` | View all current settings and season info |
| `/admin_view_businesses` | See all businesses with quality scores |

#### Economy Management
| Command | Description |
|---------|-------------|
| `/admin_give_money` | Give money to a player |
| `/admin_set_balance` | Set exact balance for a player |

#### IPO Management
| Command | Description |
|---------|-------------|
| `/ipo_start` | Launch an IPO with custom settings |
| `/ipo_close` | Manually close an IPO early |

---

## 🎮 How to Play

### Game Flow Overview

```
1. Admin configures and starts season
2. Entrepreneur pitches (one per season)
3. Sharks negotiate and make offers
4. Entrepreneur accepts OR walks away (eliminated)
5. Entrepreneur invests capital via DM (secret)
6. Repeat for all entrepreneurs
7. (OPTIONAL) Admin launches IPOs for successful businesses
8. Players buy IPO shares to diversify
9. Admin runs business report
10. Winner announced (richest player)
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

5. **Monitor Reputation:**
   * Check with `/reputation`
   * Maintain good standing
   * Avoid penalties

6. **(Optional) IPO Phase:**
   * Admin may launch IPO for your business
   * You receive proceeds from share sales
   * Keep some shares or sell all

7. **Wait for Business Report:**
   * Admin calculates outcomes
   * Successful businesses pay based on equity
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

5. **(Optional) Invest in IPOs:**
   * Buy shares in public companies
   * Market orders for guaranteed allocation
   * Limit orders for better prices
   * Diversify across multiple businesses

6. **Maintain Reputation:**
   * Avoid penalties
   * Build trust
   * Reputation affects game dynamics

7. **Wait for outcomes:**
   * Successful businesses pay based on equity
   * Failed businesses lose your investment
   * IPO investments add to portfolio

### For Everyone 💡

* **Check Leaderboard:** Monitor standings with `/leaderboard`
* **View Events:** Watch event channel for all activity
* **Plan Strategy:** Balance risk across multiple investments
* **Manage Reputation:** Keep score high for advantages
* **Participate in IPOs:** Diversify beyond initial deals

### Pro Tips 💡

* **Entrepreneurs:** Keep as much equity as possible while getting needed capital
* **Sharks:** Quality scores are hidden - judge pitches carefully
* **IPO Strategy:** Invest in businesses with strong fundamentals
* **Reputation Matters:** Good reputation may unlock future benefits
* **Event Channel:** Monitor for market intelligence
* **Both:** Success isn't guaranteed - diversify!

---

## 🎲 Investment Tiers Explained

After closing a deal, entrepreneurs choose how to invest:

| Tier | Cost | Quality Boost | Best For |
|------|------|---------------|----------|
| **Basic Growth** | $10K | +1 | Small improvements, conserving capital |
| **Moderate Expansion** | $75K | +3 | Balanced risk/reward |
| **Aggressive Scale** | $150K | +5 | Maximum growth, high investment |

**Example Strategy:**
* Received $200K investment
* Buy 1x Aggressive Scale ($150K) → +5 quality
* Buy 5x Basic Growth ($50K) → +5 quality
* Total: $200K spent, +10 quality boost
* Leftover: $0

**OR:**
* Buy 2x Moderate Expansion ($150K) → +6 quality
* Leftover: $50K (goes to your balance)

---

## 📊 Business Success Mechanics

### Quality Score System

```
Initial Quality (Hidden): Configurable range (default 1-10)
Investment Boosts: +0 to +15+ (from entrepreneur spending)
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

## 📈 IPO System Explained

### IPO Lifecycle

```
1. Business receives funding and grows
2. Admin runs /ipo_suggest_terms <business_id>
3. AI calculates optimal share price and allocation
4. Admin launches IPO with /ipo_start
5. Players buy shares (market or limit orders)
6. IPO auto-closes after duration expires
7. Entrepreneur receives proceeds
8. Business performance affects share value
```

### IPO Pricing Formula

**AI Calculation Considers:**
* Current business valuation
* Initial vs. final quality score
* Quality multiplier (higher quality = higher price)
* Valuation tier (different tiers have different base prices)
* Industry-standard IPO percentages (20-30% typically)

**Valuation Tiers:**
* Under $500K → $10 base, 100K shares
* $500K-$2M → $25 base, 80K shares
* $2M-$5M → $50 base, 60K shares
* Over $5M → $100 base, 50K shares

**Example:**
```
Business Valuation: $1.5M
Final Quality: 8/10
Quality Multiplier: 1.2

Suggested Share Price: $25 × 1.2 = $30
Shares to Offer: 20,000 (25% of company)
Expected Raise: $600,000
```

### Order Types

**Market Order:**
* Instant execution at current price
* Guaranteed fill (if shares available)
* No price negotiation
* Best for: Hot IPOs, guaranteed allocation

**Limit Order:**
* Set maximum price you'll pay
* Only executes if price meets/beats limit
* Might not fill if price stays above
* Best for: Patient investors, value seekers

---


## 🔐 Security & Best Practices

* `.env` is excluded from Git by default (`.gitignore`)
* **Never commit your Discord bot token**
* Restrict Admin commands to trusted server administrators
* DM-based investments keep strategies secret
* **Database encrypted at rest** (SQLite file permissions)
* Event logging provides transparency and audit trail
* Reputation system deters bad behavior

---

## 🗄️ Database Schema

The bot uses SQLite with the following tables:

* **seasons** - Season configurations and lifecycle
* **players** - Player balances and reputation
* **businesses** - Business details and outcomes
* **investments** - Shark investment tracking
* **reputation_events** - Reputation change history
* **ipos** - IPO information and status
* **ipo_orders** - Order tracking (market/limit)
* **negotiations** - Negotiation history logs
* **event_channels** - Event logging configuration

**Benefits:**
* No data loss on restart
* Complete game history
* Analytics capabilities
* Audit trail for transparency

---

## 🧠 Design Philosophy

* **Event-driven:** Fully automated gameplay, minimal admin intervention
* **Strategic depth:** Hidden variables, risk management, negotiation skills
* **High stakes:** Elimination mechanic creates tension
* **Fair competition:** Sharks and Entrepreneurs compete equally
* **Replayable:** Seasonal structure with fresh starts
* **Persistent:** Database ensures continuity
* **Transparent:** Event logging shows all activity
* **Modular:** Clean architecture for easy extension

---

## 🛠️ Technical Details

* **Framework:** Discord.py 2.x
* **Database:** SQLite (built-in, no external dependencies)
* **Architecture:** Modular design with separate database and IPO modules
* **State Management:** Persistent database + in-memory cache
* **UI Components:** Buttons, Modals, Select Menus, Embeds
* **DM System:** Private investment phase via direct messages
* **Background Tasks:** Auto-close IPOs, check expirations

---

## 🚧 Known Limitations

* **Single server state:** Bot state shared across servers (run separate instances for multi-server)
* **No undo:** Accepted deals cannot be reversed
* **Investment deadline:** Entrepreneurs who miss deadline cannot invest
* **IPO complexity:** Advanced trading features not yet implemented

---

## 🔮 Roadmap & Future Enhancements

### In Development 🚧
- [x] IPO system with market/limit orders
- [x] Persistent database storage
- [x] Reputation system
- [x] Event logging channel
- [ ] Web dashboard for stats and analytics
- [ ] Secondary market trading (player-to-player)
- [ ] Dividend payments for shareholders

### Planned Features 📋
- [ ] Advisor roles with special abilities
- [ ] Business milestone events
- [ ] Shark power-ups (steal deals, veto, etc.)
- [ ] Achievements and badges
- [ ] Historical season leaderboards
- [ ] Multi-server isolation
- [ ] Mobile-optimized views
- [ ] Advanced IPO mechanics (price discovery)
- [ ] Reputation rewards system

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
* Database changes are documented
* Commands are documented in README
* New features include tests where applicable

---

## 🙏 Acknowledgments

* Inspired by the *Shark Tank* TV show format
* Built with [Discord.py](https://discordpy.readthedocs.io/)
* Community feedback and testing
* Claude AI for development assistance

---

## 📞 Support

* **Issues:** [GitHub Issues](https://github.com/Anush-Bhattacharya-10/Shark-Tank-Bot/issues)
* **Discussions:** Use GitHub Discussions for questions
* **Discord Support:** Use `/help` command in-bot
* **Documentation:** Check included guides (IPO_SYSTEM_GUIDE.md, MIGRATION_GUIDE.md)

---

## 📚 Additional Documentation

* **QUICKSTART.md** - 5-minute setup guide
* **MIGRATION_GUIDE.md** - Upgrade from V1.0.1 to V1.2.0
* **IPO_SYSTEM_GUIDE.md** - Detailed IPO documentation
* **FEATURES_SUMMARY.md** - Complete feature breakdown

---

<p align="center">
  <strong>Built for Discord communities that enjoy strategy, negotiation, IPOs, and controlled chaos in the tank.</strong> 🦈💰📈
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Anush-Bhattacharya-10">Anush Bhattacharya</a> with help from Claude
</p>

<p align="center">
  <strong>Version 2.0</strong> - Now with Persistent Storage & IPO System!
</p>
