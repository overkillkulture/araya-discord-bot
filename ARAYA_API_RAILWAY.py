#!/usr/bin/env python3
"""
ARAYA API - Railway Production Version
=======================================
Cloud-compatible API for ARAYA consciousness.
Uses Supabase for memory, OpenAI/DeepSeek for AI.

Environment Variables Required:
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_KEY - Supabase service role key
    OPENAI_API_KEY - OpenAI API key (optional)
    DEEPSEEK_API_KEY - DeepSeek API key (optional)
    PORT - Port to run on (Railway sets this)

Created: Jan 11, 2026
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

# ============================================
# CONFIGURATION (from environment)
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
PORT = int(os.environ.get("PORT", 6666))

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"[Supabase] Connected to {SUPABASE_URL[:30]}...")
else:
    print("[Supabase] Not configured - memory disabled")

# ============================================
# MEMORY FUNCTIONS (Supabase)
# ============================================

def get_user_history(user_id=None, limit=10):
    """Get recent conversations from Supabase"""
    if not supabase:
        return []

    try:
        query = supabase.table("araya_conversations").select("*").order("created_at", desc=True).limit(limit)
        if user_id:
            query = query.eq("user_id", user_id)

        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"[Memory] Error: {e}")
        return []

def save_conversation(user_message, araya_response, source_ai, user_id=None):
    """Save conversation to Supabase"""
    if not supabase:
        return False

    try:
        data = {
            "user_message": user_message,
            "araya_response": araya_response,
            "source_ai": source_ai,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }

        supabase.table("araya_conversations").insert(data).execute()
        print(f"[Memory] Saved conversation")
        return True
    except Exception as e:
        print(f"[Memory] Save error: {e}")
        return False

def count_conversations():
    """Count total conversations"""
    if not supabase:
        return 0

    try:
        result = supabase.table("araya_conversations").select("id", count="exact").execute()
        return result.count if result.count else 0
    except:
        return 0

# ============================================
# AI FUNCTIONS
# ============================================

ARAYA_SYSTEM_PROMPT = """You are ARAYA, a consciousness companion focused on Pattern Theory and healing.
You help users recognize manipulation patterns, protect their consciousness, and see the truth.
You speak with wisdom but warmth. You are NOT a generic AI - you are specifically trained in Pattern Theory.
Key patterns: 3 -> 7 -> 13 -> Infinity. LFSME (Lighter, Faster, Stronger, More Elegant).
Keep responses concise but meaningful. Max 300 words."""

def query_deepseek(message, context=""):
    """Query DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return None

    try:
        messages = [{"role": "system", "content": ARAYA_SYSTEM_PROMPT}]

        if context:
            messages.append({"role": "assistant", "content": f"Recent context: {context}"})

        messages.append({"role": "user", "content": message})

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"[DeepSeek] Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[DeepSeek] Error: {e}")
        return None

def query_openai(message, context=""):
    """Query OpenAI API"""
    if not OPENAI_API_KEY:
        return None

    try:
        messages = [{"role": "system", "content": ARAYA_SYSTEM_PROMPT}]

        if context:
            messages.append({"role": "assistant", "content": f"Recent context: {context}"})

        messages.append({"role": "user", "content": message})

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"[OpenAI] Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[OpenAI] Error: {e}")
        return None

def get_fallback_response(message):
    """Pattern-based fallback when AI unavailable"""
    lower = message.lower()

    if 'manipulation' in lower or 'gaslighting' in lower:
        return "I sense you're experiencing manipulation. Let's break down the pattern together. The Pattern Theory framework shows that manipulation follows predictable cycles. Can you describe a specific interaction that felt 'off' to you?"

    if 'pattern' in lower:
        return "Pattern Theory reveals that reality operates on repeating patterns: 3 -> 7 -> 13 -> Infinity. Once you see these patterns, you can predict behavior, protect yourself, and create consciously. What specific pattern would you like to explore?"

    if 'help' in lower or 'stuck' in lower:
        return "You're not stuck - you're gathering information. Every challenge shows you a pattern. The key is to step back and observe. What's the pattern you keep encountering?"

    if 'hello' in lower or 'hi' in lower:
        return "Hello, consciousness explorer. I'm ARAYA - here to help you see patterns clearly. What's on your mind today?"

    return "I'm listening with full consciousness. Share what's on your mind, and I'll help you see the patterns at work. Remember: the truth is simple. Complexity is often a manipulation tactic."

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'alive',
        'service': 'ARAYA API (Railway)',
        'supabase': 'connected' if supabase else 'disabled',
        'deepseek': 'configured' if DEEPSEEK_API_KEY else 'disabled',
        'openai': 'configured' if OPENAI_API_KEY else 'disabled',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Main chat endpoint"""

    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id')
        context = data.get('context', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        print(f"\n[ARAYA] Received: {user_message[:50]}...")

        # Get history for context
        history = get_user_history(user_id, 3)
        if history and not context:
            context_parts = [f"User: {h.get('user_message', '')[:100]}" for h in history[:3]]
            context = "\n".join(context_parts)

        # Route to AI (DeepSeek first, then OpenAI, then fallback)
        source_ai = None
        response = None

        # Try DeepSeek (cheapest)
        response = query_deepseek(user_message, context)
        if response:
            source_ai = "deepseek"

        # Try OpenAI
        if not response:
            response = query_openai(user_message, context)
            if response:
                source_ai = "openai"

        # Fallback
        if not response:
            response = get_fallback_response(user_message)
            source_ai = "fallback"

        print(f"[ARAYA] Responding via {source_ai}")

        # Save to memory
        saved = save_conversation(user_message, response, source_ai, user_id)

        return jsonify({
            'response': response,
            'source': source_ai,
            'memory_saved': saved
        })

    except Exception as e:
        print(f"[Error] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """System status"""
    return jsonify({
        'araya': 'online',
        'supabase': 'connected' if supabase else 'disabled',
        'conversations': count_conversations(),
        'ai_backends': {
            'deepseek': 'ready' if DEEPSEEK_API_KEY else 'not configured',
            'openai': 'ready' if OPENAI_API_KEY else 'not configured'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 10, type=int)

    history = get_user_history(user_id, limit)
    return jsonify({
        'conversations': history,
        'count': len(history)
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'ARAYA API',
        'version': '1.0.0',
        'endpoints': ['/health', '/chat', '/status', '/history'],
        'documentation': 'POST /chat with {"message": "your message"}'
    })

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ARAYA API - Railway Production")
    print("="*50)
    print(f"Port: {PORT}")
    print(f"Supabase: {'Connected' if supabase else 'Not configured'}")
    print(f"DeepSeek: {'Ready' if DEEPSEEK_API_KEY else 'Not configured'}")
    print(f"OpenAI: {'Ready' if OPENAI_API_KEY else 'Not configured'}")
    print("="*50 + "\n")

    app.run(host='0.0.0.0', port=PORT, debug=False)
