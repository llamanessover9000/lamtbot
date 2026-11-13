import os
import discord
import random
import sqlite3
import csv
import re
from discord.ext import commands
from dotenv import load_dotenv

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

bot.run(TOKEN)