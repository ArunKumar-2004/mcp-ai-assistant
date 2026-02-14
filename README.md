# 🚀 AI Deployment Readiness Assistant (MCP Server)

The **AI Deployment Readiness Assistant** is a powerful MCP server that audits your CI/CD builds, configuration drift, and service health to determine if a project is ready for production.

## ✨ Features

- **AI Log Analysis**: Automatically identifies root causes for build failures.
- **Config Drift Detection**: Compares staging vs. production configurations.
- **Deep Health Checks**: Validates service endpoints and database connectivity.
- **Multi-Project Support**: Audit any project in your organization from a single server.

## 🚀 Instant Usage (No Cloning)

Run this server directly from GitHub without cloning. Add this to your IDE's MCP settings:

- **Command**: `npx`
- **Args**: `["-y", "github:ArunKumar-2004/mcp-ai-assistant"]`
- **Env**: (Add your `GITHUB_TOKEN`, `COHERE_API_KEY`, etc. here)

### ⚠️ Troubleshooting "Python not found" (Windows)

If you get a **Code 9009** or "Python was not found":

1. Open **Start Menu**, search for **"Manage App Execution Aliases"**.
2. Find `Python.exe` and `Python3.exe` in the list.
3. **Turn them OFF**.
4. Restart your IDE and try again.

---

## 🛠️ Usage & External Setup

To use this MCP server on any machine (including your own or a colleague's):

### 1. Installation

```bash
git clone https://github.com/your-username/readiness-assistant.git
cd readiness-assistant
python -m venv .venv
# Activate: source .venv/bin/activate (Mac/Linux) or .venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### 2. Configure Secrets

Create a `.env` file based on `.env.example`:

```env
COHERE_API_KEY=your_key
GITHUB_TOKEN=your_token
SLACK_WEBHOOK_URL=your_webhook
```

### 3. Initialize Schema

Initialize or copy the example schema:

```bash
python server.py --init-config
# OR
cp readiness_schema.json.example readiness_schema.json
```

### 4. Connect to IDE (Antigravity/Cursor)

In your IDE settings, add the server pointing to **the absolute path** of `server.py`:

- **Command**: `python` (or the path to your `.venv` python)
- **Args**: `["D:/path/to/repo/server.py"]`
- **Env**: Add your keys globally or in the IDE settings.

## 🔋 Supported Tools

- `evaluate_build(project, build_id, environment)`: Full-stack audit.
- `verify_build(project, build_id)`: Log-only analysis.
- `verify_config(project, environment)`: Configuration-only audit.
- `verify_health(project, environment)`: Health-only check.
