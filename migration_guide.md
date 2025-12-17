# 🔄 Migration Guide: v1.0.1 → v1.2.0

## Quick Start (No Data Migration)

If you're starting fresh and don't need to preserve old data:

### 1. Backup Your Old Bot
```bash
cp Shark-Tank.py Shark-Tank-OLD.py
```

### 2. Add New Files
```
your-bot-folder/
├── Shark-Tank.py       # Replace with enhanced version
├── database.py         # NEW - Add this file
├── ipo_system.py       # NEW - Add this file
└── .env                # Keep your existing one
```

### 3. Run the Enhanced Bot
```bash
python Shark-Tank.py
```

The database will auto-create! That's it! 🎉

---

## With Data Migration (Preserve Existing Game)

If you have an active season and want to keep the data:

### Option A: Finish Current Season First (Recommended)

**Step 1:** Complete your current season with the old bot
```
/admin_business_report  # Generate final results
/admin_end_season       # End the season
```

**Step 2:** Switch to enhanced bot
```bash
# Add the new files
python Shark-Tank.py  # Start enhanced bot
```

**Step 3:** Configure and start new season
```
/admin_set_roles
/admin_set_event_channel
/admin_configure_season
/admin_start_season
```

### Option B: Manual Data Migration

If you must preserve mid-season data:

**Step 1:** Export current data (add to old bot temporarily)
```python
import json

# Add this command to your old bot
@bot.tree.command(name="export_data")
@app_commands.checks.has_permissions(administrator=True)
async def export_data(interaction: discord.Interaction):
    data = {
        "player_money": player_money,
        "businesses": businesses,
        "game_config": game_config,
        "eliminated_entrepreneurs": list(eliminated_entrepreneurs)
    }
    
    with open("migration_data.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    await interaction.response.send_message("Data exported to migration_data.json")
```

**Step 2:** Run export command
```
/export_data
```

**Step 3:** Create migration script
```python
# migration_script.py
import json
from database import SharkTankDB
from datetime import datetime, timedelta

db = SharkTankDB()

# Load exported data
with open("migration_data.json", "r") as f:
    data = json.load(f)

# Create season
season_settings = data["game_config"]
season_id = db.create_season(YOUR_GUILD_ID, season_settings)

# Migrate players
for user_id, balance in data["player_money"].items():
    db.upsert_player(
        int(user_id),
        f"User_{user_id}",  # You'll need to get real names
        YOUR_GUILD_ID,
        season_id,
        "shark",  # Determine actual role
        balance
    )

# Migrate businesses
for biz_id, biz in data["businesses"].items():
    db.create_business(
        biz_id,
        season_id,
        biz["entrepreneur_id"],
        biz["entrepreneur_name"],
        biz["pitch"],
        biz.get("asking_amount", 0),
        biz.get("asking_equity", 0),
        biz["initial_quality"],
        biz["valuation"],
        datetime.fromisoformat(biz["deadline"]) if "deadline" in biz else datetime.now()
    )
    
    # Update with investment data
    db.update_business_investment(
        biz_id,
        biz.get("capital_invested", 0),
        biz.get("quality_boost", 0),
        biz["final_quality"],
        biz.get("investment_complete", False)
    )
    
    # Add shark investments
    for i, shark_id in enumerate(biz["shark_ids"]):
        db.add_investment(
            biz_id,
            shark_id,
            biz["shark_names"][i],
            biz["investment"] / len(biz["shark_ids"]),
            biz["equity_given"] / len(biz["shark_ids"]),
            ""
        )

print(f"Migration complete! Season ID: {season_id}")
```

**Step 4:** Run migration
```bash
python migration_script.py
```

**Step 5:** Update enhanced bot
```python
# In Shark-Tank.py, after bot starts, manually set:
game_config["season_id"] = YOUR_MIGRATED_SEASON_ID
game_config["season_active"] = True
```

---

## Key Differences Between Versions

### What's New
✅ Persistent database (SQLite)
✅ Reputation system
✅ IPO functionality
✅ Event logging channel
✅ Admin business viewing (private)
✅ Configurable quality ranges
✅ Penalty system
✅ Season configuration wizard
✅ Better data persistence

### What's the Same
✅ All original commands work
✅ Pitch system unchanged
✅ Negotiation flow identical
✅ Investment tiers same
✅ Business calculation same
✅ User interface unchanged

### What Changed
🔄 Data stored in database (not just memory)
🔄 Some admin commands have more options
🔄 Event logging optional but recommended
🔄 Season starts require configuration step

---

## Testing the Migration

### 1. Test Basic Commands
```
/help          # Should show new features
/balance       # Check balance works
/leaderboard   # View rankings
```

### 2. Test Admin Commands
```
/admin_config           # View configuration
/admin_view_business    # Should work with existing businesses
/reputation             # New command
```

### 3. Test Database
```python
# Check database was created
ls shark_tank.db  # Should exist

# Verify data
from database import SharkTankDB
db = SharkTankDB()
season = db.get_active_season(YOUR_GUILD_ID)
print(season)
```

### 4. Test New Features
```
/ipo_list              # Should show no IPOs initially
/reputation            # Check your reputation
/admin_set_event_channel  # Set logging channel
```

---

## Rollback Plan

If something goes wrong:

### Quick Rollback
```bash
# Stop the enhanced bot
# Start the old bot
python Shark-Tank-OLD.py
```

### Restore from Backup
```bash
cp Shark-Tank-OLD.py Shark-Tank.py
rm shark_tank.db  # Remove new database
# Your in-memory data returns
```

---

## Common Migration Issues

### Issue: Commands not syncing
**Solution:**
```python
# Wait 1-2 minutes after bot starts
# Or restart bot
# Discord caches commands
```

### Issue: Database errors
**Solution:**
```bash
# Delete database and recreate
rm shark_tank.db
python Shark-Tank.py  # Auto-creates fresh DB
```

### Issue: Missing player data
**Solution:**
```
# Players need to interact once to be added
# Or admin can use /admin_give_money to create them
/admin_give_money user:@Player amount:0
```

### Issue: Old data not showing
**Solution:**
```python
# Check if migration script ran
# Verify season_id is set correctly
# Check database with:
sqlite3 shark_tank.db "SELECT * FROM seasons;"
```

---

## Post-Migration Checklist

After migrating, verify:

- [ ] Bot connects successfully
- [ ] All commands sync (wait 2 min)
- [ ] Roles configured (`/admin_set_roles`)
- [ ] Event channel set (optional)
- [ ] Season active (`/admin_config`)
- [ ] Player balances correct (`/balance`)
- [ ] Businesses visible (`/admin_view_businesses`)
- [ ] Database file exists (`shark_tank.db`)
- [ ] New features accessible:
  - [ ] `/reputation`
  - [ ] `/ipo_list`
  - [ ] `/admin_penalize`
  - [ ] `/admin_reveal_quality`

---

## Support & Troubleshooting

### Check Logs
```bash
# Bot console shows errors
# Look for:
# - Import errors (missing modules)
# - Database errors (permissions)
# - Discord API errors (token/permissions)
```

### Database Issues
```bash
# Check database exists and is writable
ls -la shark_tank.db

# View database schema
sqlite3 shark_tank.db ".schema"

# Query data
sqlite3 shark_tank.db "SELECT * FROM seasons;"
```

### Module Import Errors
```bash
# Ensure all files in same directory
ls database.py ipo_system.py Shark-Tank.py

# Check Python can import
python -c "import database; import ipo_system"
```

---

## Recommended Migration Path

**For Most Users:**
```
1. Finish current season with old bot
2. Replace files with enhanced versions
3. Start fresh season with new features
```

**Why?**
- Cleanest migration
- No data conflicts
- Test all features properly
- Players get fresh start

**Timeline:**
- Day 1: Announce upcoming changes
- Day 2-3: Finish current season
- Day 4: Deploy enhanced bot
- Day 5: Configure and start new season

---

## Feature Adoption Strategy

Don't enable everything at once! Gradual rollout:

### Phase 1: Core Features (Week 1)
- Database storage (automatic)
- Event logging channel
- Season configuration

### Phase 2: Advanced Features (Week 2)
- Reputation system
- Quality range reveals
- Penalty commands

### Phase 3: IPO System (Week 3+)
- Introduce IPO concept
- Run first IPO
- Let players learn trading

This gives players time to learn new features!

---

## Questions?

Common questions:

**Q: Will old data be lost?**
A: In-memory data (from old bot) won't persist unless migrated. Recommend fresh start.

**Q: Can I run both bots?**
A: No - same bot token can't run twice. Choose one.

**Q: Do I need to migrate?**
A: No! You can start fresh with enhanced bot anytime.

**Q: What if migration fails?**
A: Rollback to old bot, troubleshoot, try again.

**Q: How long does migration take?**
A: With script: 5-10 minutes. Fresh start: Instant.

---

**Good luck with your migration! 🦈🚀**