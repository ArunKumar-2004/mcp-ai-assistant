# 🚀 AI Deployment Readiness Assistant (MCP Server)

The **AI Deployment Readiness Assistant** is a powerful MCP server that audits your CI/CD builds, configuration drift, and service health to determine if a project is ready for production.

## ✨ Features

- **AI Log Analysis**: Automatically identifies root causes for build failures.
- **Config Drift Detection**: Compares staging vs. production configurations.
- **Deep Health Checks**: Validates service endpoints and database connectivity.
- **Multi-Project Support**: Audit any project in your organization from a single server.

## 🛠️ Usage from GitHub

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/readiness-assistant.git
cd readiness-assistant
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file based on `.env.example`:

```env
COHERE_API_KEY=your_key
GITHUB_TOKEN=your_token
SLACK_WEBHOOK_URL=your_webhook
```

### 3. Setup Project Schema

Initialize your `readiness_schema.json`:

```bash
python server.py --init-config
```

Edit the generated file to include your project repos and health URLs.

### 4. Connect to your IDE (Antigravity/Cursor/Claude)

Add the following to your MCP settings:

```json
{
  "mcp_servers": {
    "readiness-assistant": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "COHERE_API_KEY": "...",
        "GITHUB_TOKEN": "..."
      }
    }
  }
}
```

## 🔋 Supported Tools

- `evaluate_build(project, build_id, environment)`: Full-stack audit.
- `verify_build(project, build_id)`: Log-only analysis.
- `verify_config(project, environment)`: Configuration-only audit.
- `verify_health(project, environment)`: Health-only check.
