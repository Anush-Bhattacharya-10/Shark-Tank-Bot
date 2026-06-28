# Privacy Policy

🛡️ **Last Updated:** June 2026  
🔒 **Data Governance:** Transparent & Privacy-First

---

Your privacy is critically important to us. Because the **Shark Tank Discord Bot** operates completely within the Discord ecosystem, this policy outlines exactly what public data we process to run your game session.

---

### 📊 1. Data We Process
To support active game loops, leaderboards, and portfolio calculations, the Bot handles basic public identifiers supplied via the official Discord API:

| Data Type | Purpose | Scope |
| :--- | :--- | :--- |
| **Discord User ID** | To accurately assign cash balances, portfolio investments, and business ownership to a specific player. | Kept in local memory/file |
| **Server (Guild) ID** | To isolate separate game sessions so different Discord servers don't blend economies. | Kept in local memory/file |
| **Role IDs** | To verify permissions for the `/pitch` command (Entrepreneurs) and investment prompts (Sharks). | Read-only check |
| **Display Names** | To render beautifully organized leaderboards (`/leaderboard`) and public channel deal announcements. | Visually displayed |

### ⚙️ 2. How We Use Your Data
Data usage is strictly functional. We use your public identifiers to map database entries—like tracking who owns a particular business or how much virtual cash a Shark has left. **We do not collect personal text messages, track your location, or build behavioral user profiles.**

### 💾 3. Storage & Security
* **No Cloud Databases:** Data is stored locally on the host machine running the script (using localized system memory or lightweight structured text/JSON files).
* **Zero External Sharing:** We do not monetarily exploit, sell, rent, or distribute any public Discord data to third-party tracking networks or advertisers.

### 🧼 4. Data Retention & Deletion
* **Instant Resets:** Server administrators can wipe all stored player data, balances, and portfolios at any time by triggering the `/admin_start_season` command.
* **Hard Deletions:** If you want your historical game profile scrubbed from a specific server's instance, request a local cache wipe from the host administrator.

### 🌐 5. Third-Party Frameworks
Because this application runs through the Discord platform, your use of the Bot is simultaneously subject to the global [Discord Privacy Policy](https://discord.com/privacy).