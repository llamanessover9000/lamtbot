import os
import discord
import random
import sqlite3
import csv
import re
from discord.ext import commands
from dotenv import load_dotenv
import time
from datetime import datetime
from discord.ext import commands, tasks
from reminders import parse_when, TZ

from database import db, setup_tables
from courses import load_courses
from nerd_baseline import load_nerd_baseline

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=";", intents=intents)

setup_tables()
COURSE_MAP = load_courses()
load_nerd_baseline()
MATH_KEYWORDS = [
    "deriv", "int", "matrix", "theorem", "proof","add", "minus", "subtract", 
    "eigenvalue", "vector", "polynomial", "equation", "calc", "anal", 
    "symmetric", "topology", "algebra", "direct", "laplace", "kernel", "image",
    "linalg", "differentiable", "multi", "coeff", "product", "inverse", "mod", "contradiction",
    "abelian", "cyclic", "sylow", "group", "ring", "field", "math", "meth", "orz", "xooks", 
    "function", "bijection", "map", "equal", "set", "riemann", "number", "comb", "geo", "theory",
    "markov", "abstract", "statistic", "weierstrass", "probability", "dirichlet", "resolvent", 
    "qed", "residue", "tensor", "linear", "quadratic", "differential", "eigen", "homotopy", "homology", 
    "map", "morphism", "functor", "object", "category", "homomorphism", "embedding", "monomorphism", 
    "epimorphism", "monoid", "yoneda", "endofunctor", "adjoint", "monad", "limit", "sign"
]

MATH_KEYWORD_PATTERN = re.compile(
    "|".join(MATH_KEYWORDS),
    re.IGNORECASE
)

ALLOWED_CHANNEL_IDS = {
    1550394906231574608,  # botslop
}

async def safe_react(message, emoji):
    try:
        await message.add_reaction(emoji)
    except discord.HTTPException:
        pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong!")
    
@bot.command(ignore_extra=False)
async def rng(ctx, low: int=1, high: int=100):
    if low> high:
        await ctx.send("i think the first number cant be higher than the second lol")
        return
    result = random.randint(low, high)
    await ctx.send(str(result))

@rng.error
async def rng_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("you should prob provide integers lol")
    else:
        await ctx.send("what the heck you broke my bot - vicky")
        
@bot.command()
async def tunnel(ctx):
    await ctx.send("tunnel!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

@bot.command()
async def course(ctx, department: str, code: str):
    key = (department.upper(), code.upper())
    if key in COURSE_MAP:
        await ctx.send(f"{department.upper()} {code.upper()} is {COURSE_MAP[key]}")
    else:
        await ctx.send("i don't think this course exists in vicky's small database 🙁")
    
@course.error
async def course_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("the message format is [course name] [course code] btw")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("what the heck send a course code")
    else:
        await ctx.send("what the heck you broke my bot - vicky")    

@bot.event
async def on_message(message):
    if message.guild is None:
        return
    if message.author.bot:
        return
    if re.search(r"n+e+r+d+", message.content, re.IGNORECASE):
        db.execute("""
            INSERT INTO nerd_counts (user_id, guild_id, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET count = count + 1
        """, (message.author.id, message.guild.id))
        db.commit()
        if message.channel.id in ALLOWED_CHANNEL_IDS:
            await message.add_reaction("😦")

    if message.channel.id in ALLOWED_CHANNEL_IDS:
        if MATH_KEYWORD_PATTERN.search(message.content):
            await message.add_reaction("🤓")

    await bot.process_commands(message)

# @bot.event
# async def on_message(message):
#     if message.author == "736365448282636369":
        

@bot.command()
async def nerdcount(ctx):
    row = db.execute(
        "SELECT SUM(count) FROM nerd_counts WHERE guild_id=?",
        (ctx.guild.id,)
    ).fetchone()
    live_total = row[0] if row[0] is not None else 0
    
    baseline_row=db.execute(
        "SELECT baseline FROM nerd_baseline_server WHERE guild_id=?",
        (ctx.guild.id,)
    ).fetchone()
    baseline=baseline_row[0] if baseline_row else 0
    
    await ctx.send(f"these bigahh nerds have said 'nerd' {live_total+baseline} times, what big nerds")

@bot.command()
async def nerdcountuser(ctx, member: discord.Member = None):
    member = member or ctx.author
    row = db.execute(
        "SELECT count FROM nerd_counts WHERE user_id=? AND guild_id=?",
        (member.id, ctx.guild.id)
    ).fetchone()
    live_count = row[0] if row else 0
    
    baseline_row = db.execute(
        "SELECT baseline FROM nerd_baseline_user WHERE user_id=? AND guild_id=?",
        (member.id, ctx.guild.id)
    ).fetchone()
    baseline = baseline_row[0] if baseline_row else 0
    
    await ctx.send(f"this nerd {member.display_name} has said 'nerd' {live_count+baseline} times what a nerd")

# =====================================================
# reminders and shiii

SAFE_MENTIONS = discord.AllowedMentions(everyone=False, roles=False)

@bot.command(help="Set a reminder, e.g. ;remind 24h study  or  ;remind feb 27 ong lamt")
async def remind(ctx, *, text: str):
    now = datetime.now(TZ)
    parsed = parse_when(text, now)
    if parsed is None:
        await ctx.send("I couldn't read that time. Try `;remind 30m take a break` or `;remind feb 27 ong its lamt`.")
        return
    when, content = parsed
    if when <= now:
        await ctx.send("bro im not a time traveller")
        return
    if not content:
        content = "(no message)"

    ts = int(when.timestamp())
    db.execute("""
        INSERT INTO reminders (user_id, guild_id, channel_id, message_id, remind_at, created_at, content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ctx.author.id, ctx.guild.id, ctx.channel.id, ctx.message.id, ts, int(now.timestamp()), content))
    db.commit()
    await ctx.message.reply(f"Got it, I'll remind you <t:{ts}:R> (<t:{ts}:f>).", mention_author=False)


@tasks.loop(seconds=30)
async def check_reminders():
    due = db.execute(
        "SELECT id, user_id, channel_id, message_id, created_at, content FROM reminders WHERE remind_at <= ?",
        (int(time.time()),)
    ).fetchall()

    for rid, user_id, channel_id, message_id, created_at, content in due:
        channel = bot.get_channel(channel_id)
        if channel is None:  # channel was deleted or isn't cached
            db.execute("DELETE FROM reminders WHERE id = ?", (rid,))
            continue
        text = f"<@{user_id}> reminder from <t:{created_at}:R>: {content}"
        try:
            original = await channel.fetch_message(message_id)
            await original.reply(text, allowed_mentions=SAFE_MENTIONS)
        except discord.NotFound:  # original message was deleted, so just post in the channel
            await channel.send(text, allowed_mentions=SAFE_MENTIONS)
        except discord.HTTPException as e:
            print(f"Reminder {rid} failed: {e}")
            continue  # leave it in the database and retry next loop
        db.execute("DELETE FROM reminders WHERE id = ?", (rid,))
    db.commit()
    
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not check_reminders.is_running():
        check_reminders.start()
        
@remind.error
async def remind_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `;remind 24h study` or `;remind feb 27 ong lamt`")
    else:
        await ctx.send("what did you do 😦")
        
        
@bot.command(help="List your pending reminders.")
async def reminders(ctx):
    rows = db.execute(
        "SELECT id, remind_at, content FROM reminders WHERE user_id = ? AND guild_id = ? ORDER BY remind_at",
        (ctx.author.id, ctx.guild.id)
    ).fetchall()
    if not rows:
        await ctx.send("You have no pending reminders.")
        return
    lines = [f"`{rid}` — <t:{ts}:R>: {content[:80]}" for rid, ts, content in rows]
    await ctx.send("\n".join(lines)[:1900], allowed_mentions=discord.AllowedMentions.none())

@bot.command(help="Cancel one of your reminders by id, e.g. ;unremind 3")
async def unremind(ctx, reminder_id: int):
    cur = db.execute(
        "DELETE FROM reminders WHERE id = ? AND user_id = ?",
        (reminder_id, ctx.author.id)
    )
    db.commit()
    if cur.rowcount:
        await ctx.send(f"Cancelled reminder {reminder_id}.")
    else:
        await ctx.send("You don't have a reminder with that id.")

@unremind.error
async def unremind_error(ctx, error):
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send("Usage: `;unremind <id>`. Use `;reminders` to see your ids.")

bot.run(TOKEN)