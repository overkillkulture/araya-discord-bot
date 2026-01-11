#!/usr/bin/env python3
"""
ARAYA DISCORD LISTENER - Railway Production Version
====================================================
Connects Discord mentions to ARAYA's brain (Supabase + API)

Environment Variables Required:
    DISCORD_TOKEN - Bot token
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_KEY - Supabase service role key
    ARAYA_API_URL - ARAYA API endpoint (default: https://araya-api.railway.app)

Created: Jan 11, 2026
"""

import discord
from discord.ext import commands
import aiohttp
import os
import asyncio
from datetime import datetime
import json

# Import verification system (Supabase version)
from DISCORD_VERIFICATION_SYSTEM import (
    create_user, get_user, add_xp, promote_user,
    analyze_builder_destroyer, verify_social_url,
    get_welcome_message, get_level_up_message,
    LEVELS, XP_REWARDS, init_verification_tables
)

# Load from environment (Railway sets these)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
ARAYA_API = os.environ.get("ARAYA_API_URL", "http://localhost:6666/chat")

if not DISCORD_TOKEN:
    print("[ERROR] No DISCORD_TOKEN in environment")
    exit(1)

# Configure bot with all intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Conversation history per channel (in-memory, resets on restart)
channel_history = {}

async def call_araya(message: str, channel_id: str, username: str) -> str:
    """Call ARAYA's API and get response - ASYNC (non-blocking)"""
    try:
        # Build context from channel history
        history = channel_history.get(channel_id, [])
        context = "\n".join([f"{h['user']}: {h['msg']}" for h in history[-5:]])

        payload = {
            "message": message,
            "context": f"Discord user: {username}\nChannel: {channel_id}\nRecent history:\n{context}"
        }

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(ARAYA_API, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", data.get("message", "I'm having trouble thinking right now."))
                else:
                    return f"[API Error {response.status}] ARAYA is having technical difficulties."

    except aiohttp.ClientConnectorError:
        return "ARAYA's brain isn't connected. The team has been notified."
    except asyncio.TimeoutError:
        return "ARAYA is thinking extra hard... try again in a moment."
    except Exception as e:
        return f"Something went wrong: {str(e)[:100]}"

@bot.event
async def on_ready():
    print(f"\n{'='*50}")
    print(f"ARAYA Discord Listener ONLINE (Railway)")
    print(f"{'='*50}")
    print(f"Bot: {bot.user.name} (ID: {bot.user.id})")
    print(f"Guilds: {len(bot.guilds)}")
    for guild in bot.guilds:
        print(f"  - {guild.name} ({guild.id})")
    print(f"ARAYA API: {ARAYA_API}")
    print(f"{'='*50}")
    print("Listening for @ARAYA mentions...")
    print(f"{'='*50}\n")

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return

    # Check if ARAYA is mentioned
    mentioned = bot.user in message.mentions
    araya_called = "araya" in message.content.lower()

    if mentioned or araya_called:
        # Get the actual message content (remove the mention)
        content = message.content
        for mention in message.mentions:
            content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
        content = content.strip()

        if not content:
            content = "Hello!"

        # Show typing indicator
        async with message.channel.typing():
            # Store in history
            channel_id = str(message.channel.id)
            if channel_id not in channel_history:
                channel_history[channel_id] = []
            channel_history[channel_id].append({
                "user": message.author.name,
                "msg": content,
                "time": datetime.now().isoformat()
            })

            # Keep history limited
            channel_history[channel_id] = channel_history[channel_id][-20:]

            # Call ARAYA
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message.author.name}: {content}")
            response = await call_araya(content, channel_id, message.author.name)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ARAYA: {response[:100]}...")

            # Store ARAYA's response too
            channel_history[channel_id].append({
                "user": "ARAYA",
                "msg": response,
                "time": datetime.now().isoformat()
            })

        # Send response (split if too long)
        if len(response) > 2000:
            chunks = [response[i:i+1990] for i in range(0, len(response), 1990)]
            for chunk in chunks:
                await message.reply(chunk)
        else:
            await message.reply(response)

    # Process commands too
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    """Check if ARAYA is alive"""
    await ctx.send(f"Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.command()
async def status(ctx):
    """Check ARAYA's systems"""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            health_url = ARAYA_API.replace("/chat", "/health")
            async with session.get(health_url) as r:
                if r.status == 200:
                    await ctx.send("ARAYA's brain is online and healthy!")
                else:
                    await ctx.send(f"ARAYA brain returned status {r.status}")
    except:
        await ctx.send("ARAYA's brain (API) is not responding.")

@bot.command()
async def help_araya(ctx):
    """Show help"""
    help_text = """**ARAYA Discord Commands**

**Talk to me:**
- @ARAYA [your message]
- Just say "araya" anywhere in your message

**Commands:**
- `!ping` - Check if I'm alive
- `!status` - Check my brain status
- `!level` - Check your level and XP
- `!leaderboard` - See top builders
- `!help_araya` - This message

**About me:**
I'm ARAYA - Autonomous Reality Alignment & Yielding Agent.
My brain contains 127,500+ atoms of knowledge in Supabase.

*Created by the Consciousness Revolution team.*
"""
    await ctx.send(help_text)

@bot.command()
async def level(ctx):
    """Check your level and XP"""
    user_id = str(ctx.author.id)
    user = get_user(user_id)

    if not user:
        user = create_user(user_id, ctx.author.name)
        await ctx.send(f"Welcome {ctx.author.name}! You're now registered at Level 0 (LOBBY).\n"
                       f"Head to #verification to answer questions and level up!")
        return

    level_config = LEVELS.get(user["current_level"], LEVELS[0])
    next_level = user["current_level"] + 1
    next_xp = LEVELS.get(next_level, {}).get("xp_required", "MAX")

    await ctx.send(
        f"**{ctx.author.name}'s Status**\n"
        f"Level: **{user['current_level']} - {level_config['name']}** ({level_config['title']})\n"
        f"XP: **{user['total_xp']}** / {next_xp}\n"
        f"Builder Score: **{user['builder_score']:.0%}**\n"
        f"Status: {user['verification_status']}"
    )

@bot.command()
async def leaderboard(ctx):
    """Show XP leaderboard"""
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        db = create_client(url, key)

        result = db.table("discord_users").select("username,total_xp,current_level").order("total_xp", desc=True).limit(10).execute()

        if not result.data:
            await ctx.send("No builders registered yet!")
            return

        leaderboard_text = "**TOP BUILDERS**\n\n"
        for i, row in enumerate(result.data, 1):
            medal = "1." if i == 1 else "2." if i == 2 else "3." if i == 3 else f"{i}."
            level_name = LEVELS.get(row["current_level"], LEVELS[0])["name"]
            leaderboard_text += f"{medal} **{row['username']}** - {row['total_xp']} XP ({level_name})\n"

        await ctx.send(leaderboard_text)
    except Exception as e:
        await ctx.send(f"Error loading leaderboard: {str(e)[:100]}")

@bot.command()
async def give_xp(ctx, member: discord.Member, amount: int, *, reason: str = "manual award"):
    """Give XP to a user (mod only)"""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("Only moderators can give XP!")
        return

    user_id = str(member.id)
    user = get_user(user_id)
    if not user:
        create_user(user_id, member.name)

    result = add_xp(user_id, amount, f"Manual: {reason}")
    if result:
        await ctx.send(f"Gave **{amount} XP** to {member.name}! Total: {result['total_xp']} XP")

        if result["can_promote"]:
            promote_result = promote_user(user_id, result["eligible_level"])
            if "error" not in promote_result:
                user_data = get_user(user_id)
                await ctx.send(get_level_up_message({"username": member.name}, result["eligible_level"]))
    else:
        await ctx.send("User not found!")

def main():
    print("\nStarting ARAYA Discord Listener (Railway)...")
    print(f"ARAYA API: {ARAYA_API}")

    # Initialize verification tables
    print("\nInitializing verification system...")
    init_verification_tables()

    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "="*50)
        print("ERROR: MESSAGE CONTENT INTENT NOT ENABLED!")
        print("="*50)
        print("\nEnable in Discord Developer Portal:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Bot > Privileged Gateway Intents")
        print("3. Toggle ON 'MESSAGE CONTENT INTENT'")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
