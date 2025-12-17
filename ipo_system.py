import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

class IPOSystem:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def calculate_ipo_terms(self, business_valuation: float, equity_given: float,
                           initial_quality: int, final_quality: int) -> Dict:
        """
        Calculate suggested IPO terms based on business metrics
        
        Returns suggested share price, total shares, and valuation
        """
        # Base share price calculation
        # Higher quality businesses get higher share prices
        quality_multiplier = (final_quality / 10) * 1.5
        
        # Determine share price tiers based on valuation
        if business_valuation < 500000:
            base_price = 10
            total_shares = 100000
        elif business_valuation < 2000000:
            base_price = 25
            total_shares = 80000
        elif business_valuation < 5000000:
            base_price = 50
            total_shares = 60000
        else:
            base_price = 100
            total_shares = 50000
        
        suggested_price = base_price * quality_multiplier
        
        # Calculate what percentage of company to IPO (typically 20-30%)
        ipo_percentage = 25  # Default 25%
        shares_to_offer = int(total_shares * (ipo_percentage / 100))
        
        # Calculate expected raise
        expected_raise = suggested_price * shares_to_offer
        
        return {
            "suggested_share_price": round(suggested_price, 2),
            "total_shares": total_shares,
            "shares_to_offer": shares_to_offer,
            "ipo_percentage": ipo_percentage,
            "expected_raise": round(expected_raise, 2),
            "post_ipo_valuation": business_valuation,
            "quality_score": final_quality
        }
    
    def create_ipo(self, business_id: str, season_id: int, share_price: float,
                   total_shares: int, available_shares: int, duration_hours: int) -> int:
        """
        Create a new IPO
        
        Returns ipo_id
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        cursor.execute("""
            INSERT INTO ipos (business_id, season_id, share_price, total_shares,
                            available_shares, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        """, (business_id, season_id, share_price, total_shares, available_shares,
              start_time, end_time))
        
        ipo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ipo_id
    
    def get_ipo(self, ipo_id: int) -> Optional[Dict]:
        """Get IPO details"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ipos WHERE ipo_id = ?", (ipo_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'ipo_id': row[0],
                'business_id': row[1],
                'season_id': row[2],
                'share_price': row[3],
                'total_shares': row[4],
                'available_shares': row[5],
                'start_time': row[6],
                'end_time': row[7],
                'status': row[8],
                'created_at': row[9]
            }
        return None
    
    def get_active_ipo_for_business(self, business_id: str) -> Optional[Dict]:
        """Get active IPO for a business"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ipos 
            WHERE business_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (business_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'ipo_id': row[0],
                'business_id': row[1],
                'season_id': row[2],
                'share_price': row[3],
                'total_shares': row[4],
                'available_shares': row[5],
                'start_time': row[6],
                'end_time': row[7],
                'status': row[8],
                'created_at': row[9]
            }
        return None
    
    def get_all_active_ipos(self, season_id: int) -> List[Dict]:
        """Get all active IPOs for a season"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ipos 
            WHERE season_id = ? AND status = 'active'
            ORDER BY start_time DESC
        """, (season_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'ipo_id': row[0],
            'business_id': row[1],
            'season_id': row[2],
            'share_price': row[3],
            'total_shares': row[4],
            'available_shares': row[5],
            'start_time': row[6],
            'end_time': row[7],
            'status': row[8],
            'created_at': row[9]
        } for row in rows]
    
    def place_market_order(self, ipo_id: int, user_id: int, username: str,
                          shares_requested: int) -> Tuple[bool, str, Optional[int]]:
        """
        Place a market order (buy at current price immediately)
        
        Returns: (success, message, order_id)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get IPO details
        ipo = self.get_ipo(ipo_id)
        if not ipo:
            return False, "IPO not found", None
        
        if ipo['status'] != 'active':
            return False, "IPO is not active", None
        
        # Check if IPO has ended
        if datetime.now() > datetime.fromisoformat(ipo['end_time']):
            return False, "IPO has ended", None
        
        # Check available shares
        if shares_requested > ipo['available_shares']:
            return False, f"Only {ipo['available_shares']} shares available", None
        
        # Calculate cost
        total_cost = shares_requested * ipo['share_price']
        
        # Create order
        cursor.execute("""
            INSERT INTO ipo_orders (ipo_id, user_id, username, order_type,
                                   shares_requested, price_per_share, shares_filled,
                                   total_cost, status)
            VALUES (?, ?, ?, 'market', ?, ?, ?, ?, 'filled')
        """, (ipo_id, user_id, username, shares_requested, ipo['share_price'],
              shares_requested, total_cost))
        
        order_id = cursor.lastrowid
        
        # Update available shares
        cursor.execute("""
            UPDATE ipos 
            SET available_shares = available_shares - ?
            WHERE ipo_id = ?
        """, (shares_requested, ipo_id))
        
        conn.commit()
        conn.close()
        
        return True, f"Order filled: {shares_requested} shares at ${ipo['share_price']} each", order_id
    
    def place_limit_order(self, ipo_id: int, user_id: int, username: str,
                         shares_requested: int, limit_price: float) -> Tuple[bool, str, Optional[int]]:
        """
        Place a limit order (buy only if price meets or beats limit)
        
        Returns: (success, message, order_id)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get IPO details
        ipo = self.get_ipo(ipo_id)
        if not ipo:
            return False, "IPO not found", None
        
        if ipo['status'] != 'active':
            return False, "IPO is not active", None
        
        # Check if limit price is met
        if limit_price < ipo['share_price']:
            # Place pending order
            cursor.execute("""
                INSERT INTO ipo_orders (ipo_id, user_id, username, order_type,
                                       shares_requested, price_per_share, shares_filled,
                                       total_cost, status)
                VALUES (?, ?, ?, 'limit', ?, ?, 0, 0, 'pending')
            """, (ipo_id, user_id, username, shares_requested, limit_price))
            
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, f"Limit order placed: {shares_requested} shares at ${limit_price}", order_id
        else:
            # Execute as market order
            conn.close()
            return self.place_market_order(ipo_id, user_id, username, shares_requested)
    
    def get_user_orders(self, ipo_id: int, user_id: int) -> List[Dict]:
        """Get all orders for a user in an IPO"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ipo_orders 
            WHERE ipo_id = ? AND user_id = ?
            ORDER BY created_at DESC
        """, (ipo_id, user_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'order_id': row[0],
            'ipo_id': row[1],
            'user_id': row[2],
            'username': row[3],
            'order_type': row[4],
            'shares_requested': row[5],
            'price_per_share': row[6],
            'shares_filled': row[7],
            'total_cost': row[8],
            'status': row[9],
            'created_at': row[10]
        } for row in rows]
    
    def get_all_orders(self, ipo_id: int) -> List[Dict]:
        """Get all orders for an IPO"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ipo_orders 
            WHERE ipo_id = ?
            ORDER BY created_at ASC
        """, (ipo_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'order_id': row[0],
            'ipo_id': row[1],
            'user_id': row[2],
            'username': row[3],
            'order_type': row[4],
            'shares_requested': row[5],
            'price_per_share': row[6],
            'shares_filled': row[7],
            'total_cost': row[8],
            'status': row[9],
            'created_at': row[10]
        } for row in rows]
    
    def cancel_order(self, order_id: int, user_id: int) -> Tuple[bool, str]:
        """Cancel a pending order"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if order exists and belongs to user
        cursor.execute("""
            SELECT status FROM ipo_orders 
            WHERE order_id = ? AND user_id = ?
        """, (order_id, user_id))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Order not found"
        
        if row[0] != 'pending':
            conn.close()
            return False, f"Cannot cancel {row[0]} order"
        
        # Cancel order
        cursor.execute("""
            UPDATE ipo_orders 
            SET status = 'cancelled'
            WHERE order_id = ?
        """, (order_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Order cancelled successfully"
    
    def close_ipo(self, ipo_id: int) -> Tuple[bool, str, Dict]:
        """
        Close an IPO and return summary
        
        Returns: (success, message, summary_dict)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get IPO details
        ipo = self.get_ipo(ipo_id)
        if not ipo:
            return False, "IPO not found", {}
        
        if ipo['status'] != 'active':
            return False, "IPO is not active", {}
        
        # Update status
        cursor.execute("""
            UPDATE ipos 
            SET status = 'closed', end_time = ?
            WHERE ipo_id = ?
        """, (datetime.now(), ipo_id))
        
        # Cancel all pending orders
        cursor.execute("""
            UPDATE ipo_orders 
            SET status = 'cancelled'
            WHERE ipo_id = ? AND status = 'pending'
        """, (ipo_id,))
        
        # Get summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(shares_filled) as total_shares_sold,
                SUM(total_cost) as total_raised,
                COUNT(DISTINCT user_id) as unique_investors
            FROM ipo_orders
            WHERE ipo_id = ? AND status = 'filled'
        """, (ipo_id,))
        
        summary_row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        summary = {
            'total_orders': summary_row[0] or 0,
            'total_shares_sold': summary_row[1] or 0,
            'total_raised': summary_row[2] or 0,
            'unique_investors': summary_row[3] or 0,
            'shares_remaining': ipo['available_shares'],
            'share_price': ipo['share_price']
        }
        
        return True, "IPO closed successfully", summary
    
    def get_ipo_summary(self, ipo_id: int) -> Dict:
        """Get current IPO summary statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(shares_filled) as total_shares_sold,
                SUM(total_cost) as total_raised,
                COUNT(DISTINCT user_id) as unique_investors
            FROM ipo_orders
            WHERE ipo_id = ? AND status IN ('filled', 'partial')
        """, (ipo_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        ipo = self.get_ipo(ipo_id)
        
        return {
            'total_orders': row[0] or 0,
            'total_shares_sold': row[1] or 0,
            'total_raised': row[2] or 0,
            'unique_investors': row[3] or 0,
            'shares_available': ipo['available_shares'] if ipo else 0,
            'total_shares': ipo['total_shares'] if ipo else 0,
            'share_price': ipo['share_price'] if ipo else 0,
            'status': ipo['status'] if ipo else 'unknown'
        }
    
    def check_expired_ipos(self, season_id: int) -> List[int]:
        """
        Check for expired IPOs and auto-close them
        
        Returns list of closed IPO IDs
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now()
        
        # Find expired IPOs
        cursor.execute("""
            SELECT ipo_id FROM ipos 
            WHERE season_id = ? AND status = 'active' AND end_time < ?
        """, (season_id, current_time))
        
        expired_ipo_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Close each expired IPO
        closed_ids = []
        for ipo_id in expired_ipo_ids:
            success, _, _ = self.close_ipo(ipo_id)
            if success:
                closed_ids.append(ipo_id)
        
        return closed_ids