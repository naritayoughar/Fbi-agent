import os
import discord
import requests
import random
from discord.ext import commands
from datetime import timedelta

# ================= CONFIG =================

CONFIG_URL = "https://raw.githubusercontent.com/naritayoughar/Fbi-agent/main/config.json"

try:
    r = requests.get(CONFIG_URL, timeout=10)
    r.raise_for_status()
    CFG = r.json()
    print("CONFIG LOADED")
except Exception as e:
    print("CONFIG ERROR:", e)
    exit(1)

# ================= DISCORD =================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= MEMORY DB =================

DB = {}

def get_strikes(uid):
    return DB.get(uid, 0)

def add_strike(uid):
    DB[uid] = get_strikes(uid) + 1

# ================= EVENTS =================

@bot.event
async def on_ready():
    print("FBI AGENT | ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    text = message.content.lower()

    if any(word in text for word in CFG["keywords"]):
        add_strike(message.author.id)
        strikes = get_strikes(message.author.id)

        penalty = CFG["penalties"][min(strikes - 1, len(CFG["penalties"]) - 1)]
        audio_file = random.choice(CFG["audio_files"])

        await message.channel.send(
            f"⚠️ مخالفة مسجلة\nالعدد: {strikes}",
            file=discord.File(audio_file)
        )

        sec = discord.utils.get(
            message.guild.text_channels,
            name=CFG["security_channel"]
        )

        if sec:
            await sec.send(
                f"""🚨 FBI AGENT REPORT
👤 User: {message.author}
🆔 ID: {message.author.id}
💬 Message: {message.content}
🔢 Strikes: {strikes}
⚖️ Penalty: {penalty}
"""
            )

        if penalty == "BAN":
            await message.guild.ban(
                message.author,
                reason="Auto moderation | FBI AGENT"
            )
        else:
            await message.author.timeout(
                timedelta(seconds=int(penalty)),
                reason="Auto moderation | FBI AGENT"
            )

    await bot.process_commands(message)

# ================= COMMAND =================

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    DB.pop(member.id, None)
    await ctx.send("✅ تم مسح سجل العضو")

# ================= RUN =================

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ضع التوكن في Environment Variable باسم DISCORD_TOKEN")
    exit(1)

bot.run(TOKEN)    print("CONFIG LOADED")
except Exception as e:
    print("CONFIG ERROR:", e)
    exit(1)

# ================= DISCORD =================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= MEMORY DB =================

DB = {}

def get_strikes(uid):
    return DB.get(uid, 0)

def add_strike(uid):
    DB[uid] = get_strikes(uid) + 1

# ================= EVENTS =================

@bot.event
async def on_ready():
    print("FBI AGENT | ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    text = message.content.lower()

    if any(word in text for word in CFG["keywords"]):
        add_strike(message.author.id)
        strikes = get_strikes(message.author.id)

        penalty = CFG["penalties"][min(strikes - 1, len(CFG["penalties"]) - 1)]
        audio_file = random.choice(CFG["audio_files"])

        await message.channel.send(
            f"⚠️ مخالفة مسجلة\nالعدد: {strikes}",
            file=discord.File(audio_file)
        )

        sec = discord.utils.get(
            message.guild.text_channels,
            name=CFG["security_channel"]
        )

        if sec:
            await sec.send(
                f"""🚨 FBI AGENT REPORT
👤 User: {message.author}
🆔 ID: {message.author.id}
💬 Message: {message.content}
🔢 Strikes: {strikes}
⚖️ Penalty: {penalty}
"""
            )

        if penalty == "BAN":
            await message.guild.ban(
                message.author,
                reason="Auto moderation | FBI AGENT"
            )
        else:
            await message.author.timeout(
                timedelta(seconds=int(penalty)),
                reason="Auto moderation | FBI AGENT"
            )

    await bot.process_commands(message)

# ================= COMMAND =================

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    DB.pop(member.id, None)
    await ctx.send("✅ تم مسح سجل العضو")

# ================= RUN =================
٦
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ضع التوكن في Environment Variable باسم DISCORD_TOKEN")
    exit(1)

bot.run(DISCORD_TOKEN)
