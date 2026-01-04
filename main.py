import discord
from discord.ext import commands
from datetime import timedelta
import requests, random, json, io, os

# 🔹 روابط RAW الصحيحة من GitHub
CONFIG_RAW_URL = "https://raw.githubusercontent.com/naritayoughar/Fbi-agent/main/config.json"

try:
    CFG = requests.get(CONFIG_RAW_URL).json()
except Exception as e:
    print("Error loading config:", e)
    exit(1)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DB = {}  # قاعدة بيانات مؤقتة للمخالفات

def strikes(uid):
    return DB.get(uid, 0)

def add_strike(uid):
    DB[uid] = strikes(uid) + 1

@bot.event
async def on_ready():
    print("FBI AGENT | ONLINE")

@bot.event
async def on_message(msg):
    if msg.author.bot or not msg.guild:
        return

    content = msg.content.lower()
    if any(word.lower() in content for word in CFG["keywords"]):
        add_strike(msg.author.id)
        s = strikes(msg.author.id)

        # الحصول على العقوبة
        penalty = CFG["penalties"][min(s-1, len(CFG["penalties"])-1)]

        # اختيار ملف صوتي عشوائي
        audio_url = random.choice(CFG["audio_urls"])
        r = requests.get(audio_url)
        audio = io.BytesIO(r.content)

        # إرسال التحذير في الشات
        await msg.channel.send(
            f"⚠️ Violation detected | مخالفة مسجلة\nStrikes: {s}",
            file=discord.File(audio, filename="warning.mp3")
        )

        # إرسال التقرير لقناة الأمن
        sec_channel = discord.utils.get(msg.guild.text_channels, name=CFG["security_channel"])
        if sec_channel:
            await sec_channel.send(
                f"User: {msg.author}\n"
                f"Strikes: {s}\n"
                f"Message: {msg.content}\n"
                f"Penalty: {penalty}"
            )

        # تنفيذ العقوبة
        if str(penalty).upper() == "BAN":
            await msg.guild.ban(msg.author, reason="Auto moderation")
        else:
            await msg.author.timeout(
                timedelta(seconds=int(penalty)),
                reason="Auto moderation"
            )

    await bot.process_commands(msg)

# أمر لمسح سجل عضو
@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    DB.pop(member.id, None)
    await ctx.send(f"Record cleared | تم مسح السجل: {member}")

# تشغيل البوت
bot.run(os.getenv("DISCORD_TOKEN"))
