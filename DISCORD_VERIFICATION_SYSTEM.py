#!/usr/bin/env python3
"""
DISCORD VERIFICATION SYSTEM - Supabase Version for Railway
============================================================
Multi-Tier Trust + XP Gates using Supabase PostgreSQL
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client

# Supabase connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = None

def get_supabase():
    global supabase
    if supabase is None:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

# ============================================================
# LEVEL CONFIGURATION
# ============================================================

LEVELS = {
    0: {
        "name": "LOBBY",
        "title": "Newcomer",
        "xp_required": 0,
        "color": "#808080",
        "channels": ["verification", "introductions", "araya-chat"],
        "perks": ["Can chat with ARAYA", "Read-only most channels"]
    },
    1: {
        "name": "SEEDLING",
        "title": "Verified Human",
        "xp_required": 50,
        "color": "#90EE90",
        "channels": ["lounge", "how-to-help", "wins-your-mission-update"],
        "perks": ["Can chat in lounge", "Can claim simple tasks"]
    },
    2: {
        "name": "SAPLING",
        "title": "Active Builder",
        "xp_required": 200,
        "color": "#32CD32",
        "channels": ["task-board", "bug-reports", "tutorials"],
        "perks": ["Can claim any task", "Can report bugs", "Voice access"]
    },
    3: {
        "name": "TREE",
        "title": "Trusted Builder",
        "xp_required": 500,
        "color": "#228B22",
        "channels": ["t1-builders", "t2-architects", "revenue-streams"],
        "perks": ["Trinity hub access", "Can assign tasks to others"]
    },
    4: {
        "name": "FOREST",
        "title": "Core Team",
        "xp_required": 1000,
        "color": "#006400",
        "channels": ["crypto-launch", "alerts"],
        "perks": ["Financial discussions", "Strategy input"]
    },
    5: {
        "name": "ORACLE",
        "title": "Inner Circle",
        "xp_required": 2500,
        "color": "#7c3aed",
        "channels": ["command-center", "audit-log", "moderator-only"],
        "perks": ["Full access", "Admin capabilities", "Direct comms"]
    }
}

# Builder/Destroyer indicators
BUILDER_PATTERNS = [
    "help", "build", "create", "contribute", "offer", "share", "support",
    "collaborate", "team", "together", "improve", "solution", "fix"
]

DESTROYER_PATTERNS = [
    "fake", "scam", "stupid", "dumb", "hate", "attack", "destroy",
    "waste", "useless", "never", "impossible", "can't", "won't"
]

# ============================================================
# DATABASE FUNCTIONS (Supabase)
# ============================================================

def init_verification_tables():
    """Tables created via SQL - this just validates connection"""
    try:
        db = get_supabase()
        # Test connection
        result = db.table("discord_users").select("user_id").limit(1).execute()
        print(f"Verification system connected to Supabase")
        return True
    except Exception as e:
        print(f"Warning: discord_users table may not exist: {e}")
        return False

def get_user(user_id: str) -> dict:
    """Get user data from Supabase"""
    try:
        db = get_supabase()
        result = db.table("discord_users").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            row = result.data[0]
            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "joined_at": row["joined_at"],
                "current_level": row["current_level"],
                "total_xp": row["total_xp"],
                "verification_status": row["verification_status"],
                "social_verified": row.get("social_verified", False),
                "social_url": row.get("social_url"),
                "builder_score": row.get("builder_score", 0.5),
                "last_active": row.get("last_active"),
                "notes": row.get("notes")
            }
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def create_user(user_id: str, username: str) -> dict:
    """Create new user in lobby"""
    try:
        db = get_supabase()
        now = datetime.now().isoformat()

        data = {
            "user_id": user_id,
            "username": username,
            "joined_at": now,
            "current_level": 0,
            "total_xp": 0,
            "verification_status": "pending",
            "last_active": now
        }

        db.table("discord_users").upsert(data).execute()
        return get_user(user_id)
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def add_xp(user_id: str, amount: int, reason: str) -> dict:
    """Add XP and check for level up"""
    try:
        db = get_supabase()
        user = get_user(user_id)

        if not user:
            return None

        new_xp = user["total_xp"] + amount
        now = datetime.now().isoformat()

        # Log XP
        db.table("xp_log").insert({
            "user_id": user_id,
            "xp_amount": amount,
            "reason": reason,
            "timestamp": now
        }).execute()

        # Update user
        db.table("discord_users").update({
            "total_xp": new_xp,
            "last_active": now
        }).eq("user_id", user_id).execute()

        # Check for level up eligibility
        eligible_level = get_eligible_level(new_xp)

        return {
            "user_id": user_id,
            "xp_added": amount,
            "total_xp": new_xp,
            "current_level": user["current_level"],
            "eligible_level": eligible_level,
            "can_promote": eligible_level > user["current_level"]
        }
    except Exception as e:
        print(f"Error adding XP: {e}")
        return None

def get_eligible_level(xp: int) -> int:
    """Get highest level user is eligible for based on XP"""
    eligible = 0
    for level, config in LEVELS.items():
        if xp >= config["xp_required"]:
            eligible = level
    return eligible

def promote_user(user_id: str, to_level: int, promoted_by: str = "system") -> dict:
    """Promote user to new level"""
    try:
        db = get_supabase()
        user = get_user(user_id)

        if not user:
            return {"error": "User not found"}

        # Check XP requirement
        if user["total_xp"] < LEVELS[to_level]["xp_required"]:
            return {"error": f"Not enough XP. Need {LEVELS[to_level]['xp_required']}, have {user['total_xp']}"}

        now = datetime.now().isoformat()

        # Log promotion
        db.table("promotion_log").insert({
            "user_id": user_id,
            "from_level": user["current_level"],
            "to_level": to_level,
            "promoted_by": promoted_by,
            "timestamp": now
        }).execute()

        # Update level
        db.table("discord_users").update({
            "current_level": to_level
        }).eq("user_id", user_id).execute()

        return {
            "user_id": user_id,
            "from_level": user["current_level"],
            "to_level": to_level,
            "new_title": LEVELS[to_level]["title"],
            "new_channels": LEVELS[to_level]["channels"]
        }
    except Exception as e:
        print(f"Error promoting user: {e}")
        return {"error": str(e)}

def analyze_builder_destroyer(text: str) -> dict:
    """Analyze text for builder/destroyer patterns"""
    text_lower = text.lower()

    builder_count = sum(1 for p in BUILDER_PATTERNS if p in text_lower)
    destroyer_count = sum(1 for p in DESTROYER_PATTERNS if p in text_lower)

    total = builder_count + destroyer_count
    if total == 0:
        score = 0.5  # Neutral
    else:
        score = builder_count / total

    return {
        "builder_count": builder_count,
        "destroyer_count": destroyer_count,
        "builder_score": round(score, 2),
        "classification": "BUILDER" if score > 0.6 else "DESTROYER" if score < 0.4 else "NEUTRAL"
    }

def verify_social_url(url: str) -> dict:
    """Basic social URL verification"""
    trusted_domains = [
        "twitter.com", "x.com", "linkedin.com", "instagram.com",
        "facebook.com", "github.com", "youtube.com", "tiktok.com"
    ]

    url_lower = url.lower()
    is_valid = any(domain in url_lower for domain in trusted_domains)

    return {
        "url": url,
        "is_valid": is_valid,
        "needs_human_review": True,
        "note": "Human should check: profile exists, has history, consistent identity"
    }

# ============================================================
# DISCORD INTEGRATION HELPERS
# ============================================================

def get_welcome_message(username: str) -> str:
    """Generate welcome message for new user"""
    return f"""Welcome to the Consciousness Revolution, **{username}**!

You're currently in the **LOBBY** (Level 0). To unlock more channels and features, please answer a few questions:

**1. What brings you here?** What are you hoping to accomplish?
**2. What skills do you bring?** (coding, design, writing, marketing, etc.)
**3. Are you here to:** BUILD / GET HELP / EXPLORE / CONTRIBUTE?
**4. Share a social media link** so we can verify you're a real human with history.

Once verified, you'll unlock:
- Level 1 (50 XP): Lounge access, simple tasks
- Level 2 (200 XP): Task board, bug reports
- Level 3 (500 XP): Trinity Hub, revenue discussions

Type your answers here and ARAYA will process them!"""

def get_level_up_message(user: dict, new_level: int) -> str:
    """Generate level up congratulations"""
    config = LEVELS[new_level]
    return f"""**LEVEL UP!**

**{user['username']}** has reached **Level {new_level}: {config['name']}**!

**Title:** {config['title']}
**New Channels:** {', '.join(config['channels'])}
**Perks:** {', '.join(config['perks'])}

Keep building! Next level at {LEVELS.get(new_level + 1, {}).get('xp_required', 'MAX')} XP."""

# ============================================================
# XP REWARDS
# ============================================================

XP_REWARDS = {
    "message": 1,
    "helpful_message": 3,
    "question_answered": 10,
    "task_claimed": 5,
    "task_completed": 20,
    "bug_reported": 10,
    "bug_fixed": 50,
    "win_shared": 5,
    "social_verified": 25,
    "daily_challenge": 25,
    "referred_user": 50,
    "content_created": 30,
}
