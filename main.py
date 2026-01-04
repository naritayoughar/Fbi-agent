import os
import discord
import random
import json
import requests
from discord.ext import commands
from datetime import timedelta

# ================= LOAD CONFIG =================
CONFIG_URL = "https://raw.githubusercontent.com/naritayoughar/Fbi-agent/main/config.json"

try:
    response = requests.get(CONFIG_URL, timeout=10)
    response.raise_for_status()
    CFG = response.json()
    print("CONFIG LOADED")
except Exception as e:
    print("ERROR loading config:", e)
    exit(1)

# ================= DISCORD SETUP =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= MEMORY DB =================
USER_STRIKES = {}

def get_strikes(user_id):
    return USER_STRIKES.get(user_id, 0)

def add_strike(user_id):
    USER_STRIKES[user_id] = get_strikes(user_id) + 1

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"FBI AGENT ONLINE | Logged as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await bot.process_commands(message)

    content = message.content.lower()

    if any(word in content for word in CFG["keywords"]):
        add_strike(message.author.id)
        strikes = get_strikes(message.author.id)

        penalty = CFG["penalties"][min(strikes - 1, len(CFG["penalties"]) - 1)]
        audio_path = random.choice(CFG["audio_files"])

        # Send warning + audio
        try:
            await message.channel.send(
                f"⚠️ مخالفة مسجلة\nعدد المخالفات: {strikes}",
                file=discord.File(audio_path)
            )
        except Exception as e:
            print("Audio send error:", e)

        # Log to security channel
        sec_channel = discord.utils.get(
            message.guild.text_channels,
            name=CFG["security_channel"]
        )

        if sec_channel:
            await sec_channel.send(
                f"""🚨 FBI AGENT REPORT
👤 User: {message.author}
🆔 ID: {message.author.id}
💬 Message: {message.content}
🔢 Strikes: {strikes}
⚖️ Penalty: {penalty}
"""
            )

        # Apply punishment
        try:
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
        except Exception as e:
            print("Punishment error:", e)

# ================= COMMANDS =================
@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    USER_STRIKES.pop(member.id, None)
    await ctx.send(f"✅ تم مسح سجل {member.mention}")

# ================= RUN =================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found in Environment Variables")
    exit(1)

bot.run(TOKEN)
