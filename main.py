import discord
from discord.ext import commands
import random
import json
import os
import asyncio
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Data file for user balances
DATA_FILE = 'balances.json'

# Load or create balances
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        balances = json.load(f)
else:
    balances = {}

def save_balances():
    with open(DATA_FILE, 'w') as f:
        json.dump(balances, f, indent=4)

def get_balance(user_id):
    return balances.get(str(user_id), 1000)  # Start with 1000 coins

def set_balance(user_id, amount):
    balances[str(user_id)] = amount
    save_balances()

@bot.event
async def on_ready():
    print(f'✅ Gambling Bot is online as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="🎰 Gambling | !help"))

@bot.command(name='balance')
async def balance(ctx):
    """Check your balance"""
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💰 **{ctx.author.name}**, your balance is **{bal}** coins!")

@bot.command(name='daily')
async def daily(ctx):
    """Claim daily reward (once per 24 hours)"""
    user_id = str(ctx.author.id)
    # Simple cooldown tracking (in-memory, resets on bot restart)
    if not hasattr(bot, 'daily_cooldown'):
        bot.daily_cooldown = {}
    
    last_claim = bot.daily_cooldown.get(user_id)
    now = datetime.now()
    
    if last_claim and now - last_claim < timedelta(days=1):
        time_left = (last_claim + timedelta(days=1) - now)
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        await ctx.send(f"⏳ You already claimed today! Next claim in **{hours}h {minutes}m**.")
        return
    
    reward = random.randint(500, 1500)
    current = get_balance(ctx.author.id)
    set_balance(ctx.author.id, current + reward)
    bot.daily_cooldown[user_id] = now
    
    await ctx.send(f"🎁 **Daily reward!** You received **{reward}** coins! New balance: **{current + reward}**")

@bot.command(name='slots')
async def slots(ctx, bet: int = 100):
    """Play slots! Bet amount (default 100)"""
    if bet < 10:
        await ctx.send("❌ Minimum bet is 10 coins!")
        return
    
    bal = get_balance(ctx.author.id)
    if bal < bet:
        await ctx.send("❌ Not enough coins!")
        return
    
    set_balance(ctx.author.id, bal - bet)
    
    # Slot symbols
    symbols = ['🍒', '🍋', '🍊', '⭐', '🔔', '💎', '7️⃣']
    result = [random.choice(symbols) for _ in range(3)]
    
    # Calculate winnings
    if result[0] == result[1] == result[2]:
        if result[0] == '7️⃣':
            winnings = bet * 50
        elif result[0] == '💎':
            winnings = bet * 20
        else:
            winnings = bet * 10
        message = "🎉 **JACKPOT!**"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = bet * 3
        message = "👍 **Nice win!**"
    else:
        winnings = 0
        message = "😢 Better luck next time!"
    
    new_bal = get_balance(ctx.author.id) + winnings
    set_balance(ctx.author.id, new_bal)
    
    embed = discord.Embed(title="🎰 SLOT MACHINE", color=0xFF00FF)
    embed.add_field(name="Result", value=f"{result[0]} | {result[1]} | {result[2]}", inline=False)
    embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
    embed.add_field(name="Winnings", value=f"{winnings} coins", inline=True)
    embed.set_footer(text=f"New balance: {new_bal} coins")
    
    await ctx.send(embed=embed)
    if winnings > 0:
        await ctx.send(message)

@bot.command(name='roulette')
async def roulette(ctx, bet: int, color: str):
    """Roulette: bet amount and color (red/black/green)"""
    if bet < 10:
        await ctx.send("❌ Minimum bet 10!")
        return
    bal = get_balance(ctx.author.id)
    if bal < bet:
        await ctx.send("❌ Not enough coins!")
        return
    
    color = color.lower()
    if color not in ['red', 'black', 'green']:
        await ctx.send("❌ Choose `red`, `black`, or `green`!")
        return
    
    set_balance(ctx.author.id, bal - bet)
    
    # Spin
    spin = random.randint(0, 36)
    if spin == 0:
        landed = 'green'
    elif spin % 2 == 0:
        landed = 'red'
    else:
        landed = 'black'
    
    if color == landed:
        if landed == 'green':
            winnings = bet * 14  # Higher payout for green
        else:
            winnings = bet * 2
        set_balance(ctx.author.id, get_balance(ctx.author.id) + winnings)
        await ctx.send(f"🎡 **You won!** Landed on **{landed.upper()}** (+{winnings} coins)")
    else:
        await ctx.send(f"🎡 Landed on **{landed.upper()}**. You lost **{bet}** coins.")

@bot.command(name='coinflip')
async def coinflip(ctx, bet: int, choice: str):
    """Coin flip: bet amount and heads/tails"""
    if bet < 10:
        await ctx.send("❌ Minimum bet 10!")
        return
    bal = get_balance(ctx.author.id)
    if bal < bet:
        await ctx.send("❌ Not enough coins!")
        return
    
    choice = choice.lower()
    if choice not in ['heads', 'tails']:
        await ctx.send("❌ Choose `heads` or `tails`!")
        return
    
    set_balance(ctx.author.id, bal - bet)
    
    result = random.choice(['heads', 'tails'])
    
    if result == choice:
        winnings = bet * 2
        set_balance(ctx.author.id, get_balance(ctx.author.id) + winnings)
        await ctx.send(f"🪙 **{result.upper()}!** You won **{winnings}** coins!")
    else:
        await ctx.send(f"🪙 **{result.upper()}!** You lost **{bet}** coins.")

@bot.command(name='help')
async def help_cmd(ctx):
    embed = discord.Embed(title="🎲 Gambling Bot Commands", color=0x00FF00)
    embed.add_field(name="!balance", value="Check your coins", inline=False)
    embed.add_field(name="!daily", value="Daily reward", inline=False)
    embed.add_field(name="!slots <bet>", value="Play slots (default 100)", inline=False)
    embed.add_field(name="!roulette <bet> <red/black/green>", value="Play roulette", inline=False)
    embed.add_field(name="!coinflip <bet> <heads/tails>", value="Coin flip", inline=False)
    embed.set_footer(text="Have fun responsibly! (This is virtual currency)")
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
   if __name__ == "__main__":
 TOKEN = os.getenv('DISCORD_TOKEN')
 bot.run(TOKEN)
