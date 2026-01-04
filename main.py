import discord, requests, random, json
from discord.ext import commands
from datetime import timedelta

CONFIG_URL = "https://raw.githubusercontent.com/naritayoughar/Fbi-agent/main/config.json"
CFG = requests.get(CONFIG_URL).json()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DB = {}

def strikes(uid): return DB.get(uid, 0)
def add(uid): DB[uid] = strikes(uid) + 1

@bot.event
async def on_ready():
    print("FBI AGENT | ONLINE")

@bot.event
async def on_message(msg):
    if msg.author.bot or not msg.guild:
        return

    content = msg.content.lower()
    if any(k in content for k in CFG["keywords"]):
        add(msg.author.id)
        s = strikes(msg.author.id)
        penalty = CFG["penalties"][min(s-1, len(CFG["penalties"])-1)]

        audio_url = random.choice(CFG["audio_urls"])
        audio = requests.get(audio_url, stream=True).raw

        await msg.channel.send(
            f"⚠️ Violation detected | مخالفة مسجلة\nStrikes: {s}",
            file=discord.File(audio, filename="warning.mp3")
        )

        sec = discord.utils.get(msg.guild.text_channels, name=CFG["security_channel"])
        if sec:
            await sec.send(
                f"User: {msg.author}\n"
                f"Strike: {s}\n"
                f"Message: {msg.content}\n"
                f"Penalty: {penalty}"
            )

        if penalty == "BAN":
            await msg.guild.ban(msg.author, reason="Auto moderation")
        else:
            await msg.author.timeout(timedelta(seconds=int(penalty)), reason="Auto moderation")

    await bot.process_commands(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    DB.pop(member.id, None)
    await ctx.send("Record cleared | تم مسح السجل")

# ⛔ ضع التوكن هنا بنفسك ولا ترسله لأي أحد
bot.run("MTQ1NzIxMTc1ODUzOTE4MjEyMQ.GazdFB.8NUDk45dABRSzVq3yhjbIV43AXo9wM0a9GStg4")
