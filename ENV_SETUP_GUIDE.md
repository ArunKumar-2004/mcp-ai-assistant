# .env File Setup for MCP Server

## Quick Setup

1. **Create `.env` file in YOUR PROJECT FOLDER** (where you run your IDE from):

```env
# Required
COHERE_API_KEY=your_cohere_key_here

# GitHub Configuration
GITHUB_REPOSITORY=owner/repo
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here

# Optional
SLACK_WEBHOOK_URL=your_webhook
TARGET_DB_URL=postgresql://user:pass@localhost:5432/db
```

2. **Restart MCP Server** (restart Claude Desktop or your IDE)

3. **Test**: Say "Get my latest build" - should auto-detect repo!

## Important Notes

✅ **Correct Repository Format**: `owner/repo` (e.g., `ArunKumar-2004/Wealth-hub`)
❌ **Wrong**: `main/Wealth-hub` (main is not a username)

## How It Works

The server looks for `.env*` files in this order:

1. **Current working directory** (your project folder) - FIRST PRIORITY
2. Script directory (where server.py is located) - FALLBACK

Supports: `.env`, `.env.local`, `.env.production`, `.env.development`, etc.

## Verification

After restart, check server logs for:

```
✅ Loaded: C:\your\project\folder\.env
```

If you see:

```
⚠️  No .env* files found
```

Then create `.env` in your project folder and restart.
