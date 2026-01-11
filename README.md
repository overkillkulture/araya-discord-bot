# ARAYA Discord Bot

Discord bot for the Consciousness Revolution community with XP/leveling verification system.

## Features

- **Multi-Tier Trust System**: 6 levels from LOBBY to ORACLE
- **XP Gates**: Earn XP through engagement, unlock channels
- **Builder/Destroyer Detection**: Pattern analysis on messages
- **Supabase Backend**: Cloud PostgreSQL for production scale
- **ARAYA Integration**: Connects to ARAYA's brain API

## Levels

| Level | Name | XP Required | Perks |
|-------|------|-------------|-------|
| 0 | LOBBY | 0 | Basic chat, ARAYA access |
| 1 | SEEDLING | 50 | Lounge, simple tasks |
| 2 | SAPLING | 200 | Task board, bug reports |
| 3 | TREE | 500 | Trinity Hub, task assignment |
| 4 | FOREST | 1000 | Financial discussions |
| 5 | ORACLE | 2500 | Full access, admin |

## Commands

- `!ping` - Check if bot is alive
- `!status` - Check ARAYA brain status
- `!level` - Check your XP and level
- `!leaderboard` - Top 10 builders
- `!give_xp @user amount reason` - Award XP (mod only)
- `!help_araya` - Full help

## Environment Variables

```
DISCORD_TOKEN=your_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
ARAYA_API_URL=https://araya-api.railway.app/chat
```

## Deploy to Railway

1. Connect this repo
2. Add environment variables
3. Deploy

## Created by

Consciousness Revolution Team - Jan 2026
