# 📈 IPO System Guide

## Overview

The IPO (Initial Public Offering) system allows successful businesses to "go public" and raise additional capital by selling shares to all players.

## How It Works

### For Admins

#### 1. Get Suggested Terms
```
/ipo_suggest_terms business_id:abc123
```

This analyzes the business and suggests:
- Share price (based on quality and valuation)
- Total shares to create
- Shares to offer (typically 25% of company)
- Expected capital raise

#### 2. Launch the IPO
```
/ipo_start 
    business_id:abc123 
    share_price:50 
    shares_to_offer:10000 
    duration_hours:24
```

#### 3. Monitor Active IPOs
```
/ipo_list
```

#### 4. Close IPO (optional - auto-closes after duration)
```
/ipo_close ipo_id:1
```

### For Players

#### View Available IPOs
```
/ipo_list
```
Shows:
- Business name
- Share price
- Available shares
- Total raised so far
- Time remaining

#### Buy Shares - Market Order
```
/ipo_buy ipo_id:1 shares:100 order_type:market
```
- Buys immediately at current price
- Requires sufficient balance
- Money is deducted instantly

#### Buy Shares - Limit Order
```
/ipo_buy ipo_id:1 shares:100 order_type:limit limit_price:45
```
- Only executes if price reaches your limit
- Stays pending until price matches or IPO closes
- No money deducted until filled

## IPO Pricing Formula

### Share Price Calculation
```
Base Price (by valuation tier) × Quality Multiplier

Quality Multiplier = (final_quality / 10) × 1.5
```

### Valuation Tiers
- Under $500K → $10 base price, 100K total shares
- $500K-$2M → $25 base price, 80K total shares  
- $2M-$5M → $50 base price, 60K total shares
- Over $5M → $100 base price, 50K total shares

### Example
Business with:
- Valuation: $1.5M
- Final Quality: 8/10

Calculation:
```
Base Price: $25
Quality Multiplier: (8/10) × 1.5 = 1.2
Suggested Price: $25 × 1.2 = $30
```

## Order Types

### Market Order
- **Instant execution** at current price
- **Guaranteed fill** (if shares available)
- **Higher cost** (no negotiation)
- Best for: Quick purchases

### Limit Order
- **Set maximum price** you'll pay
- **Only fills** if price meets/beats your limit
- **Can save money** if market moves
- **Might not fill** if price stays above limit
- Best for: Patient investors

## IPO Lifecycle

```
1. Admin reviews business performance
   ↓
2. Admin gets suggested terms
   ↓
3. Admin launches IPO with custom settings
   ↓
4. Players place orders (market/limit)
   ↓
5. Orders fill based on availability
   ↓
6. IPO closes (manual or automatic)
   ↓
7. Final summary generated
```

## Strategy Tips

### For Entrepreneurs
- Higher quality → Higher share price
- More capital invested → Better quality → Better IPO terms
- IPO raises additional capital for you
- You retain majority ownership (typically 75%+)

### For Investors
- Research the business quality before investing
- Market orders guarantee shares but cost more
- Limit orders can save money but might miss out
- Diversify across multiple IPOs
- Consider time remaining (urgency)

### For Admins
- Use suggested terms as a baseline
- Adjust based on business performance
- Can run multiple IPOs simultaneously
- Set appropriate duration (24-48 hours typical)
- Monitor and close manually if needed

## IPO Summary Report

When an IPO closes, a report shows:
- Total orders placed
- Total shares sold
- Capital raised
- Number of unique investors
- Remaining shares
- Final share price

## Database Tracking

All IPO data is stored permanently:
- IPO details (price, shares, duration)
- All orders (who bought what, when)
- Order status (filled/pending/cancelled)
- Total raised and distributed

## Common Scenarios

### Scenario 1: Oversubscribed IPO
```
Shares Available: 10,000
Orders Received: 25,000 shares worth

Result: First-come, first-served
Early orders fill completely
Later orders might partially fill or remain pending
```

### Scenario 2: Undersubscribed IPO
```
Shares Available: 10,000
Orders Received: 3,000 shares worth

Result: All orders fill
7,000 shares remain available
IPO stays open until duration ends
```

### Scenario 3: Limit Order Success
```
Current Price: $50
Your Limit Order: $45, 100 shares

If price drops to $45: Order fills automatically
If price stays at $50: Order stays pending
When IPO closes: Unfilled orders cancelled
```

## Advanced Features

### Suggested Terms Algorithm
Considers:
- Current business valuation
- Initial vs final quality score
- Equity already given to sharks
- Industry-standard IPO percentages (20-30%)
- Market cap targets for different tiers

### Auto-Close System
- Background task checks every hour
- Automatically closes expired IPOs
- Cancels unfilled pending orders
- Generates closure summary
- Updates all player balances

### Order Management
Players can (future feature):
- View their order history
- Cancel pending orders
- See order fill status
- Track portfolio performance

## IPO Revenue Distribution

When IPO closes, capital raised goes to:
1. **Entrepreneur** - Receives IPO proceeds
2. **Updates Balance** - Money added to player_money
3. **Database Record** - Permanent transaction log
4. **Leaderboard Impact** - Affects final rankings

## Best Practices

### For Admins
✅ Wait until investment phase complete
✅ Use suggested terms as starting point
✅ Set realistic durations (24-72 hours)
✅ Monitor for suspicious activity
✅ Close manually if fully subscribed early

### For Entrepreneurs
✅ Invest capital wisely to boost quality
✅ Complete investment phase before IPO
✅ Higher quality = better IPO terms
✅ Reinvest IPO proceeds strategically

### For Investors
✅ Check business details before buying
✅ Don't invest more than you can afford
✅ Use limit orders for better prices
✅ Act quickly on hot IPOs
✅ Diversify your portfolio

## Troubleshooting

### "IPO not found"
- Check IPO ID is correct
- Verify IPO hasn't already closed
- Use `/ipo_list` to see active IPOs

### "Insufficient funds"
- Check your balance with `/balance`
- Consider buying fewer shares
- Use limit order at lower price

### "Only X shares available"
- IPO is almost sold out
- Buy available amount
- Try another IPO

### "Limit order not filling"
- Current price is above your limit
- Increase limit price
- Or wait for market movement

## Future Enhancements

Potential additions:
- [ ] Secondary market trading
- [ ] Dividend payments based on performance
- [ ] IPO price adjustments during offering
- [ ] Pro-rata allocation for oversubscribed IPOs
- [ ] IPO performance tracking over time
- [ ] Automated IPO scheduling

---

**Happy Investing! 📈💰**