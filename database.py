import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class SharkTankDB:
    def __init__(self, db_path="shark_tank.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Seasons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                shark_starting_money INTEGER,
                entrepreneur_starting_money INTEGER,
                investment_deadline_hours INTEGER,
                is_active BOOLEAN DEFAULT 1,
                settings_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                season_id INTEGER,
                role TEXT CHECK(role IN ('shark', 'entrepreneur', 'both')),
                current_balance REAL DEFAULT 0,
                reputation_score INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id),
                UNIQUE(user_id, season_id)
            )
        """)

        # Businesses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                business_id TEXT PRIMARY KEY,
                season_id INTEGER,
                entrepreneur_id INTEGER NOT NULL,
                entrepreneur_name TEXT,
                pitch_description TEXT,
                asking_amount REAL,
                asking_equity REAL,
                initial_quality INTEGER,
                final_quality INTEGER,
                quality_boost INTEGER DEFAULT 0,
                capital_invested REAL DEFAULT 0,
                valuation REAL,
                equity_given REAL,
                investment_complete BOOLEAN DEFAULT 0,
                deadline TIMESTAMP,
                outcome TEXT CHECK(outcome IN ('pending', 'success', 'failure')),
                final_valuation REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)

        # Investments table (shark investments in businesses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT NOT NULL,
                shark_id INTEGER NOT NULL,
                shark_name TEXT,
                amount REAL,
                equity_percentage REAL,
                conditions TEXT,
                investment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id)
            )
        """)

        # Reputation events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reputation_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER,
                user_id INTEGER NOT NULL,
                event_type TEXT,
                change_amount INTEGER,
                reason TEXT,
                admin_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)

        # IPO table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ipos (
                ipo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT NOT NULL,
                season_id INTEGER,
                share_price REAL,
                total_shares INTEGER,
                available_shares INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT CHECK(status IN ('pending', 'active', 'closed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)

        # IPO Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ipo_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ipo_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                order_type TEXT CHECK(order_type IN ('market', 'limit')),
                shares_requested INTEGER,
                price_per_share REAL,
                shares_filled INTEGER DEFAULT 0,
                total_cost REAL,
                status TEXT CHECK(status IN ('pending', 'filled', 'partial', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ipo_id) REFERENCES ipos(ipo_id)
            )
        """)

        # Negotiations log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS negotiations (
                negotiation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT NOT NULL,
                actor_name TEXT,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(business_id)
            )
        """)

        # Event log channel table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_channels (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ========== SEASON MANAGEMENT ==========
    def create_season(self, guild_id: int, settings: Dict) -> int:
        """Create a new season"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO seasons (guild_id, start_date, shark_starting_money, 
                               entrepreneur_starting_money, investment_deadline_hours, 
                               settings_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            guild_id,
            datetime.now(),
            settings.get('shark_starting_money', 1000000),
            settings.get('entrepreneur_starting_money', 0),
            settings.get('investment_deadline_hours', 48),
            json.dumps(settings)
        ))

        season_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return season_id

    def get_active_season(self, guild_id: int) -> Optional[Dict]:
        """Get the active season for a guild"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM seasons 
            WHERE guild_id = ? AND is_active = 1 
            ORDER BY season_id DESC LIMIT 1
        """, (guild_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'season_id': row[0],
                'guild_id': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'shark_starting_money': row[4],
                'entrepreneur_starting_money': row[5],
                'investment_deadline_hours': row[6],
                'is_active': row[7],
                'settings': json.loads(row[8]) if row[8] else {}
            }
        return None

    def end_season(self, season_id: int):
        """End a season"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE seasons 
            SET is_active = 0, end_date = ? 
            WHERE season_id = ?
        """, (datetime.now(), season_id))

        conn.commit()
        conn.close()

    # ========== PLAYER MANAGEMENT ==========
    def upsert_player(self, user_id: int, username: str, guild_id: int,
                      season_id: int, role: str, balance: float = 0,
                      reputation: int = 100):
        """Insert or update player"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO players (user_id, username, guild_id, season_id, role, 
                               current_balance, reputation_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, season_id) DO UPDATE SET
                current_balance = excluded.current_balance,
                reputation_score = excluded.reputation_score,
                username = excluded.username
        """, (user_id, username, guild_id, season_id, role, balance, reputation))

        conn.commit()
        conn.close()

    def get_player(self, user_id: int, season_id: int) -> Optional[Dict]:
        """Get player info"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM players 
            WHERE user_id = ? AND season_id = ?
        """, (user_id, season_id))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'player_id': row[0],
                'user_id': row[1],
                'username': row[2],
                'guild_id': row[3],
                'season_id': row[4],
                'role': row[5],
                'current_balance': row[6],
                'reputation_score': row[7]
            }
        return None

    def update_player_balance(self, user_id: int, season_id: int, new_balance: float):
        """Update player balance"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE players 
            SET current_balance = ? 
            WHERE user_id = ? AND season_id = ?
        """, (new_balance, user_id, season_id))

        conn.commit()
        conn.close()

    def get_all_players(self, season_id: int) -> List[Dict]:
        """Get all players in a season"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM players 
            WHERE season_id = ?
            ORDER BY current_balance DESC
        """, (season_id,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'player_id': row[0],
            'user_id': row[1],
            'username': row[2],
            'guild_id': row[3],
            'season_id': row[4],
            'role': row[5],
            'current_balance': row[6],
            'reputation_score': row[7]
        } for row in rows]

    # ========== BUSINESS MANAGEMENT ==========
    def create_business(self, business_id: str, season_id: int, entrepreneur_id: int,
                        entrepreneur_name: str, pitch: str, asking_amount: float,
                        asking_equity: float, initial_quality: int, valuation: float,
                        deadline: datetime):
        """Create a new business"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO businesses (business_id, season_id, entrepreneur_id, 
                                  entrepreneur_name, pitch_description, asking_amount,
                                  asking_equity, initial_quality, final_quality,
                                  valuation, outcome, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (business_id, season_id, entrepreneur_id, entrepreneur_name, pitch,
              asking_amount, asking_equity, initial_quality, initial_quality,
              valuation, deadline))

        conn.commit()
        conn.close()

    def get_business(self, business_id: str) -> Optional[Dict]:
        """Get business details"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM businesses WHERE business_id = ?", (business_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'business_id': row[0],
                'season_id': row[1],
                'entrepreneur_id': row[2],
                'entrepreneur_name': row[3],
                'pitch_description': row[4],
                'asking_amount': row[5],
                'asking_equity': row[6],
                'initial_quality': row[7],
                'final_quality': row[8],
                'quality_boost': row[9],
                'capital_invested': row[10],
                'valuation': row[11],
                'equity_given': row[12],
                'investment_complete': row[13],
                'deadline': row[14],
                'outcome': row[15],
                'final_valuation': row[16]
            }
        return None

    def update_business_investment(self, business_id: str, capital_invested: float,
                                   quality_boost: int, final_quality: int,
                                   investment_complete: bool):
        """Update business investment details"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE businesses 
            SET capital_invested = ?, quality_boost = ?, final_quality = ?,
                investment_complete = ?
            WHERE business_id = ?
        """, (capital_invested, quality_boost, final_quality,
              1 if investment_complete else 0, business_id))

        conn.commit()
        conn.close()

    def update_business_outcome(self, business_id: str, outcome: str, final_valuation: float):
        """Update business final outcome"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE businesses 
            SET outcome = ?, final_valuation = ?
            WHERE business_id = ?
        """, (outcome, final_valuation, business_id))

        conn.commit()
        conn.close()

    def get_all_businesses(self, season_id: int) -> List[Dict]:
        """Get all businesses in a season"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM businesses 
            WHERE season_id = ?
            ORDER BY created_at DESC
        """, (season_id,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'business_id': row[0],
            'season_id': row[1],
            'entrepreneur_id': row[2],
            'entrepreneur_name': row[3],
            'pitch_description': row[4],
            'asking_amount': row[5],
            'asking_equity': row[6],
            'initial_quality': row[7],
            'final_quality': row[8],
            'quality_boost': row[9],
            'capital_invested': row[10],
            'valuation': row[11],
            'equity_given': row[12],
            'investment_complete': row[13],
            'deadline': row[14],
            'outcome': row[15],
            'final_valuation': row[16]
        } for row in rows]

    # ========== INVESTMENT TRACKING ==========
    def add_investment(self, business_id: str, shark_id: int, shark_name: str,
                       amount: float, equity: float, conditions: str = ""):
        """Record a shark investment"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO investments (business_id, shark_id, shark_name, amount,
                                   equity_percentage, conditions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (business_id, shark_id, shark_name, amount, equity, conditions))

        conn.commit()
        conn.close()

    def get_business_investments(self, business_id: str) -> List[Dict]:
        """Get all shark investments for a business"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM investments WHERE business_id = ?
        """, (business_id,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'investment_id': row[0],
            'business_id': row[1],
            'shark_id': row[2],
            'shark_name': row[3],
            'amount': row[4],
            'equity_percentage': row[5],
            'conditions': row[6],
            'investment_date': row[7]
        } for row in rows]

    # ========== REPUTATION SYSTEM ==========
    def add_reputation_event(self, season_id: int, user_id: int, event_type: str,
                             change_amount: int, reason: str, admin_id: int):
        """Add a reputation event"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reputation_events (season_id, user_id, event_type, 
                                          change_amount, reason, admin_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (season_id, user_id, event_type, change_amount, reason, admin_id))

        # Update player reputation
        cursor.execute("""
            UPDATE players 
            SET reputation_score = reputation_score + ?
            WHERE user_id = ? AND season_id = ?
        """, (change_amount, user_id, season_id))

        conn.commit()
        conn.close()

    def get_reputation_history(self, user_id: int, season_id: int) -> List[Dict]:
        """Get reputation history for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM reputation_events 
            WHERE user_id = ? AND season_id = ?
            ORDER BY created_at DESC
        """, (user_id, season_id))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'event_id': row[0],
            'season_id': row[1],
            'user_id': row[2],
            'event_type': row[3],
            'change_amount': row[4],
            'reason': row[5],
            'admin_id': row[6],
            'created_at': row[7]
        } for row in rows]

    # ========== NEGOTIATIONS LOG ==========
    def add_negotiation(self, business_id: str, actor_name: str, action: str, details: str):
        """Log a negotiation event"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO negotiations (business_id, actor_name, action, details)
            VALUES (?, ?, ?, ?)
        """, (business_id, actor_name, action, details))

        conn.commit()
        conn.close()

    def get_negotiations(self, business_id: str) -> List[Dict]:
        """Get negotiation history for a business"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM negotiations 
            WHERE business_id = ?
            ORDER BY timestamp ASC
        """, (business_id,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'negotiation_id': row[0],
            'business_id': row[1],
            'actor_name': row[2],
            'action': row[3],
            'details': row[4],
            'timestamp': row[5]
        } for row in rows]

    # ========== EVENT CHANNEL ==========
    def set_event_channel(self, guild_id: int, channel_id: int):
        """Set the event logging channel"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO event_channels (guild_id, channel_id)
            VALUES (?, ?)
        """, (guild_id, channel_id))

        conn.commit()
        conn.close()

    def get_event_channel(self, guild_id: int) -> Optional[int]:
        """Get the event logging channel"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT channel_id FROM event_channels WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None