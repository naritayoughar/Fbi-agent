import discord
from discord.ext import commands
import json, os, random, time, requests
from datetime import datetime, timedelta

# ---------- Load Config from GitHub ----------
CONFIG_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/FBI_AGENT/main/config.json"
CONFIG = requests.get(CONFIG_URL).json()

TOKEN = CONFIG["token"]
PREFIX = CONFIG.get("prefix", "!")
SECURITY_CHANNEL_NAME = CONFIG.get("security_channel", "security-files")
LOG_LANG = CONFIG.get("security_log_language", "MIXED")
FEATURES = CONFIG.get("features", {})
VIOLATION_POLICY = CONFIG.get("violation_policy", {})
KEYWORDS = CONFIG.get("keywords", [])

DB_PATH = "database.json"

# ---------- Intents ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ---------- Database ----------
def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

DB = load_db()

# ---------- Helpers ----------
def now_utc():
    return datetime.utcnow()

def get_security_channel(guild):
    return discord.utils.get(guild.text_channels, name=SECURITY_CHANNEL_NAME)

def user_record(user_id):
    uid = str(user_id)
    if uid not in DB:
        DB[uid] = {"strikes": 0, "history": []}
    return DB[uid]

def format_security_log(data):
    if LOG_LANG == "AR":
        return (
            "🚨 تقرير أمني — FBI AGENT\n\n"
            f"العضو: {data['member']}\n"
            f"المعرف: {data['user_id']}\n"
            f"الرتب: {data['roles']}\n\n"
            f"نوع المخالفة: {data['violation_type']}\n"
            f"الكلمة: {data['trigger']}\n"
            f"السبب: {data['reason']}\n\n"
            f"نص الرسالة:\n{data['message']}\n\n"
            f"الإجراء: {data['action']}\n"
            f"عدد المخالفات: {data['strikes']}\n"
            f"الوقت: {data['timestamp']}"
        )
    else:
        return (
            "🚨 SECURITY REPORT — FBI AGENT\n\n"
            f"Member: {data['member']}\n"
            f"User ID: {data['user_id']}\n"
            f"Roles: {data['roles']}\n\n"
            f"Violation Type: {data['violation_type']}\n"
            f"Triggered Word: {data['trigger']}\n"
            f"Reason: {data['reason']}\n\n"
            f"Message Content:\n{data['message']}\n\n"
            f"Action Taken: {data['action']}\n"
            f"Violation Count: {data['strikes']}\n"
            f"Timestamp: {data['timestamp']}"
        )

def get_random_audio():
    folder = VIOLATION_POLICY.get("audio_folder", [])
    return random.choice(folder) if folder else None

async def apply_violation(message, keyword):
    member = message.author
    guild = message.guild
    channel = message.channel
    record = user_record(member.id)
    record["strikes"] += 1
    strikes = record["strikes"]

    # Determine penalty
    penalty = None
    for step in VIOLATION_POLICY.get("penalties", []):
        if step["strike"] == strikes:
            penalty = step
            break
    if penalty is None and VIOLATION_POLICY.get("penalties"):
        penalty = VIOLATION_POLICY["penalties"][-1]

    # Send message + random audio
    audio_url = get_random_audio()
    files = [discord.File(fp=requests.get(audio_url, stream=True).raw, filename="warn.mp3")] if audio_url else None
    warn_text = (
        f"🚨 FBI AGENT ALERT\nUser: {member.mention}\nViolation: Forbidden Word\nWord: {keyword}\n"
        f"Action: {penalty['action'].upper() if penalty else 'NONE'}\nStrike: {strikes}"
    )
    await channel.send(content=warn_text, files=files)

    # Apply moderation
    action_taken = "None"
    if penalty:
        if penalty["action"] == "timeout":
            until = now_utc() + timedelta(seconds=penalty["duration_sec"])
            await member.timeout(until, reason=VIOLATION_POLICY.get("reason"))
            action_taken = f"Timeout — {penalty['duration_sec']//60} minutes"
        elif penalty["action"] == "ban":
            await member.ban(reason=VIOLATION_POLICY.get("reason"))
            action_taken = "Permanent Ban"

    # Log history
    record["history"].append({
        "trigger": keyword,
        "message": message.content,
        "action": action_taken,
        "at": now_utc().isoformat()
    })
    save_db(DB)

    # Send security log
    sec = get_security_channel(guild)
    if sec:
        roles = ", ".join([r.name for r in member.roles if r.name != "@everyone"]) or "None"
        payload = {
            "member": str(member),
            "user_id": member.id,
            "roles": roles,
            "violation_type": "Forbidden Word",
            "trigger": keyword,
            "reason": VIOLATION_POLICY.get("reason", ""),
            "message": message.content,
            "action": action_taken,
            "strikes": strikes,
            "timestamp": now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        await sec.send(format_security_log(payload))

# ---------- Events ----------
@bot.event
async def on_ready():
    print(f"[FBI AGENT] Online as {bot.user}")

_last_trigger_time = {}

@bot.event
async def on_message(message):
    if message.author.bot and FEATURES.get("ignore_bots", True):
        return
    if not message.guild:
        return
    key = (message.author.id, message.channel.id)
    cd = FEATURES.get("cooldown_seconds", 0)
    if cd > 0:
        last = _last_trigger_time.get(key, 0)
        if time.time() - last < cd:
            return
        _last_trigger_time[key] = time.time()
    for keyword in KEYWORDS:
        if keyword.lower() in message.content.lower():
            await apply_violation(message, keyword)
            break
    await bot.process_commands(message)

# ---------- Admin Commands ----------
@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def reset_user(ctx, member: discord.Member = None):
    if member:
        DB.pop(str(member.id), None)
        save_db(DB)
        await ctx.send(f"✅ FBI AGENT: Violations reset for {member.mention}")
    else:
        DB.clear()
        save_db(DB)
        await ctx.send("✅ FBI AGENT: All database cleared!")

@bot.command(name="strikes")
@commands.has_permissions(administrator=True)
async def strikes(ctx, member: discord.Member):
    rec = DB.get(str(member.id), {"strikes": 0})
    await ctx.send(f"📄 FBI AGENT: {member.mention} strikes = {rec.get('strikes',0)}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 FBI AGENT: Online")

bot.run(TOKEN)