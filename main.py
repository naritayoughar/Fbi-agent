import discord
from discord.ext import commands
from datetime import timedelta
import requests, random, json, io, os

# تحميل الإعدادات
CONFIG_URL = "https://raw.githubusercontent.com/naritayoughar/Fbi-agent/main/config.json"
CFG = requests.get(CONFIG_URL).json()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# قاعدة بيانات مؤقتة للمخالفات (RAM)
DB = {}

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

    if any(word in content for word in CFG["keywords"]):
        add_strike(msg.author.id)
        s = strikes(msg.author.id)

        penalty = CFG["penalties"][min(s - 1, len(CFG["penalties"]) - 1)]

        # اختيار صوت عشوائي
        audio_url = random.choice(CFG["audio_urls"])
        r = requests.get(audio_url)
        audio = io.BytesIO(r.content)

        # إرسال التحذير + الصوت
        await msg.channel.send(
            f"⚠️ Violation detected | مخالفة مسجلة\n"
            f"Strikes: {s}",
            file=discord.File(audio, filename="warning.mp3")
        )

        # إرسال التقرير لقناة الأمن
        sec = discord.utils.get(msg.guild.text_channels, name=CFG["security_channel"])
        if sec:
            await sec.send(
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

# مسح سجل عضو
@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    DB.pop(member.id, None)
    await ctx.send(f"Record cleared | تم مسح السجل: {member}")

# تشغيل البوت
bot.run(os.getenv("DISCORD_TOKEN"))
