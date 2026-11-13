import os
import discord
import random
import sqlite3
import csv
import re
from discord.ext import commands
from dotenv import load_dotenv

import os
DB_PATH = os.getenv("DB_PATH", "bot.db")
db = sqlite3.connect(DB_PATH)

def setup_tables():
    db.execute("""
    CREATE TABLE IF NOT EXISTS nerd_counts (
        user_id INTEGER,
        guild_id INTEGER,
        count INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, guild_id)
        )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS nerd_baseline_server (
        guild_id INTEGER PRIMARY KEY,
        baseline INTEGER DEFAULT 0
        )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS nerd_baseline_channel (
        guild_id INTEGER,
        channel_name TEXT,
        baseline INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, channel_name)
        )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS nerd_baseline_user (
        guild_id INTEGER,
        user_id INTEGER,
        baseline INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
        )
    """)
    db.commit()
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        guild_id INTEGER,
        channel_id INTEGER,
        message_id INTEGER,
        remind_at INTEGER,
        created_at INTEGER,
        content TEXT
        )
    """)

