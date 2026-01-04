import os
import json
import random
from datetime import timedelta

import discord
from discord.ext import commands

# ================= LOAD CONFIG =================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        CFG = json.load(f)
except Exception as e:
    print(f"ERROR loading config: {e}")
    exit(1)

# ================= BOT SETUP =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= MEMORY DB =================
STRIKES = {}

def get_strikes(uid):
    return STRIKES.get(uid, 0)

def add_strike(uid):
    STRIKES[uid] = get_strikes(uid) + 1
    return STRIKES[uid]

def clear_strikes(uid):
    STRIKES.pop(uid, None)

# ================= PENALTY FORMAT =================
def format_penalty(p):
    if p == "BAN":
        return "Ban نهائي"
    s = int(p)
    if s < 60:
        return f"{s} ثواني"
    elif s < 3600:
        return f"{s // 60} دقيقة"
    elif s < 86400:
        return f"{s // 3600} ساعة"
    else:
        return f"{s // 86400} يوم"

# ================= EVENTS =================
@bot.event
async def on_ready():
    print("FBI AGENT | ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    content = message.content.lower()

    if any(word in content for word in CFG["keywords"]):
        strikes = add_strike(message.author.id)

        penalty = CFG["penalties"][min(
            strikes - 1, len(CFG["penalties"]) - 1
        )]

        penalty_text = format_penalty(penalty)

        # ===== AUDIO =====
        audio_file = random.choice(CFG["audio_files"])
        audio_path = os.path.join("audio", audio_file)

        if os.path.exists(audio_path):
            await message.channel.send(
                content=(
                    "⚠️ Violation Detected | مخالفة\n"
                    f"Strikes: {strikes}\n"
                    f"Penalty: {penalty_text}"
                ),
                file=discord.File(audio_path)
            )
        else:
            await message.channel.send(
                f"⚠️ Violation | Penalty: {penalty_text}"
            )

        # ===== SECURITY REPORT =====
        sec_channel = discord.utils.get(
            message.guild.text_channels,
            name=CFG["security_channel"]
        )

        if sec_channel:
            await sec_channel.send(
                f"""🚨 FBI AGENT REPORT
👤 User: {message.author}
🆔 ID: {message.author.id}
🏷️ Roles: {[r.name for r in message.author.roles if r.name != '@everyone']}
💬 Message: {message.content}
🔢 Strikes: {strikes}
⚖️ Penalty: {penalty_text}
"""
            )

        # ===== APPLY PUNISHMENT =====
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
            print(f"Punishment error: {e}")

    await bot.process_commands(message)

# ================= COMMANDS =================
@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def reset_user(ctx, member: discord.Member):
    clear_strikes(member.id)
    await ctx.send(
        f"🧹 Record cleared for {member.mention} | تم مسح السجل"
    )

# ================= RUN =================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found in Environment Variables")
    exit(1)

bot.run(TOKEN)
