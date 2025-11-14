import os, ssl, asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from tabulate import tabulate

from sql import SQL_OVERALL, SQL_PER_TRACK, SQL_KARMA
from models import Record, TrackBoard, KarmaEntry
from utils import create_trackboards, create_leaderboard, create_karma_leaderboard

load_dotenv()

# === HEADERS ===
HEADERS_ROW = ["Player", "Score", "Place", "Points"]
HEADERS_OVERALL = ["Player", "Points", "Payout"]
HEADERS_KARMA = ["Track", "Score"]

# === Discord ===
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# === MySQL (Fakaheda) ===
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_SSL = os.getenv("DB_SSL", "0") == "1"
DB_SSL_CA = os.getenv("DB_SSL_CA")  # volitelná cesta k CA .pem

# Intents – pro čtení zpráv musí být message_content = True
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

pool = None  # MySQL pool

async def create_pool():
    import asyncmy
    ssl_ctx = None
    if DB_SSL:
        ssl_ctx = ssl.create_default_context(cafile=DB_SSL_CA) if DB_SSL_CA else ssl.create_default_context()
    return await asyncmy.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        autocommit=True,
        minsize=1,
        maxsize=4,
        ssl=ssl_ctx,
    )

@bot.event
async def on_ready():
    global pool
    print(f"Logged in as {bot.user} — creating DB pool…")
    pool = await create_pool()
    print("DB pool ready ✅")


# ---------- Bot trigger ----------

@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    if CHANNEL_ID and message.channel.id != CHANNEL_ID:
        return

    content = message.content.strip().lower()

    # Spouštěč: zpráva začíná na "uka"
    if content.startswith("uka"):
        if pool is None:
            await message.channel.send("❌ DB pool není připravený.")
            return

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # 1) per-track with points
                    await cur.execute(SQL_PER_TRACK)
                    per_rows = await cur.fetchall()  # (TrackName, PlayerName, Score, Place, Points)

            trackboards: list[TrackBoard] = create_trackboards(per_rows)

            for t in trackboards:
                track_str = f'```\n{tabulate([[t.name]], tablefmt="rounded_grid")}\n{tabulate(t.table, headers=HEADERS_ROW, tablefmt="rounded_grid")}\n```'
                await message.channel.send(track_str)

        except Exception as e:
            await message.channel.send(f"❌ DB chyba: `{e}`")

    if content.startswith("ldb"):

        if pool is None:
            await message.channel.send("❌ DB pool není připravený.")
            return

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:

                    await cur.execute(SQL_OVERALL)
                    overall_rows = await cur.fetchall()  # (PlayerName, PlayerId, TotalPoints)

            leaderboard: list[TrackBoard] = create_leaderboard(overall_rows)

            leaderboard_str = f'```\n{tabulate([["Leaderboard"]], tablefmt="rounded_grid")}\n{tabulate(leaderboard, tablefmt="rounded_grid", headers=HEADERS_OVERALL)}\n```'
            await message.channel.send(leaderboard_str)

        except Exception as e:
            await message.channel.send(f"❌ DB chyba: `{e}`")

    if content.startswith("karma"):

        if pool is None:
            await message.channel.send("❌ DB pool není připravený.")
            return

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:

                    await cur.execute(SQL_KARMA)
                    karma_rows = await cur.fetchall()

            karma_leaderboard: list[KarmaEntry] = create_karma_leaderboard(karma_rows)

            karma_leaderboard_str = f'```\n{tabulate([["Track Score"]], tablefmt="rounded_grid")}\n{tabulate(karma_leaderboard, tablefmt="rounded_grid", headers=HEADERS_KARMA)}\n```'
            await message.channel.send(karma_leaderboard_str)

        except Exception as e:
            await message.channel.send(f"❌ DB chyba: `{e}`")

    # necháme commands extension dál zpracovat případné !příkazy
    await bot.process_commands(message)

bot.run(TOKEN)
