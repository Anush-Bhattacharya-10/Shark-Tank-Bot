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

**Shark Tank Discord Bot** is a fully interactive Discord game inspired by the *Shark Tank* TV format. Entrepreneurs pitch ideas, Sharks negotiate deals (solo or joint), capital is invested strategically, and businesses are evaluated at the end of a season to determine winners.

The bot is built entirely on **Discord Slash Commands, Buttons, Modals, and Select Menus**, requiring no manual tracking by admins once a season begins.

[Add to your servers right now!](https://discord.com/oauth2/authorize?client_id=1450522916986028072&permissions=2416003072&integration_type=0&scope=bot+applications.commands)

---

## ✨ Feature Highlights

### 🎤 Pitch & Negotiation

* One pitch per entrepreneur per season
* Real-time negotiation using buttons and modals
* Sharks can:

  * Make solo offers
  * Form **joint offers with consent-based approval**
  * Counter, accept, or walk away
* Entrepreneurs can:

  * Accept or reject offers
  * Counter-offer
  * Walk away (elimination)

### 🤝 Joint Offer Consent System

* Shark selection via dropdown menu
* All selected sharks must approve
* Any shark can decline, cancelling the joint offer

### 💰 Post-Deal Investment Phase

* Entrepreneurs invest received capital into:

  * **Basic Growth** (+1 Quality)
  * **Moderate Expansion** (+3 Quality)
  * **Aggressive Scale** (+5 Quality)
* Multiple investments allowed until capital runs out
* Remaining capital converts to balance

### 📊 Business Simulation Engine

* Each business has a hidden **quality score (1–10)**
* Quality determines:

  * Probability of success
  * Final valuation multiplier
* Automatic payout distribution to entrepreneurs and sharks

### 🏆 Seasons & Leaderboards

* Admin-controlled seasons
* Live money leaderboard
* End-of-season business report
* Final wealth leaderboard

---

## 🧑‍💼 Required Discord Roles

| Role             | Permissions                |
| ---------------- | -------------------------- |
| **Shark**        | Make offers, invest money  |
| **Entrepreneur** | Pitch businesses           |
| **Admin**        | Manage seasons and economy |

Role IDs are supplied via environment variables.

---

## 📂 Project Structure

```text
├── Shark-Tank.py        # Main bot logic
├── start.bat           # Starts the bot (online)
├── stop.bat            # Stops the bot (offline)
├── .env                # Environment variables (ignored)
├── .venv/              # Virtual environment (ignored)
└── tank.ico            # Optional icon asset
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Anush-Bhattacharya-10/Shark-Tank-Bot.git
cd Shark-Tank-Bot
```

### 2️⃣ Create & Activate Virtual Environment (Recommended)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
SHARK_ROLE_ID=123456789012345678
ENTREPRENEUR_ROLE_ID=123456789012345678
```

---

## ▶️ Running the Bot

### ✅ Start (Bring Bot Online)

```bash
start.bat
```

Starts the bot and syncs all slash commands.

### ⛔ Stop (Take Bot Offline)

```bash
stop.bat
```

Safely terminates the bot process.

---

## 🧾 Slash Commands

### 👤 Player Commands

* `/pitch` – Pitch a business idea
* `/balance` – Check your balance
* `/leaderboard` – View top players
* `/status` – View current pitch status
* `/invest` – Invest capital into business growth
* `/finish_investing` – End investment phase early

### 🛡️ Admin Commands

* `/admin_start_season`
* `/admin_end_season`
* `/admin_business_report`
* `/admin_config`
* `/admin_set_shark_money`
* `/admin_set_deadline`
* `/admin_give_money`
* `/admin_set_balance`

---

## 🔐 Security & Best Practices

* `.env` is excluded from Git by default
* Never commit your Discord bot token
* Restrict Admin commands to trusted roles

---

## 🧠 Design Principles

* Event-driven, fully automated gameplay
* Minimal admin intervention during seasons
* Focus on negotiation, strategy, and risk
* Replayable seasonal structure

---

## 📜 License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute it.

---

## 🤝 Contributing

Contributions are welcome.

If you extend the bot (e.g. multi-round pitching, advisors, veto power, persistence), please document your changes clearly.

---

**Built for Discord communities that enjoy strategy, negotiation, and controlled chaos in the tank.** 🦈
