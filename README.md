# 🚀 AI Deployment Readiness Assistant (MCP Server)

The **AI Deployment Readiness Assistant** is a powerful MCP server that audits your CI/CD builds, configuration drift, and service health to determine if a project is ready for production.

## ✨ Features

- **AI-Powered Build Analysis**: Automatically fetches and analyzes GitHub Actions builds with root cause identification
- **Multi-Database Support**: PostgreSQL, MySQL, and MongoDB connectivity checks with auto-detection
- **Config Drift Detection**: Compares configurations across environments (supports JSON, YAML, .env, XML, Dockerfile)
- **Deep Health Checks**: Validates service endpoints with latency measurements
- **Intelligent Diagnostics**: All results narrated by Cohere AI for actionable insights

## 🚀 Quick Start (No Cloning Required)

Run this server directly from GitHub. Add to your MCP settings (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "readiness-assistant": {
      "command": "npx",
      "args": ["-y", "github:ArunKumar-2004/mcp-ai-assistant"],
      "env": {
        "COHERE_API_KEY": "your_cohere_api_key",
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_REPOSITORY": "owner/repo",
        "SLACK_WEBHOOK_URL": "your_slack_webhook",
        "TARGET_DB_URL": "postgresql://user:pass@host:5432/db"
      }
    }
  }
}
```

> [!CAUTION]
> **Security Warning**: Never commit API keys to public repositories. Use your IDE's secret storage.

### ⚠️ Troubleshooting \"Python not found\" (Windows)

If you get **Code 9009** or \"Python was not found\":

1. Open **Start Menu** → **\"Manage App Execution Aliases\"**
2. Find `Python.exe` and `Python3.exe`
3. **Turn them OFF**
4. Restart your IDE

---

## 🛠️ Local Development Setup

### 1. Installation

```bash
git clone https://github.com/ArunKumar-2004/mcp-ai-assistant.git
cd mcp-ai-assistant
pip install -e .
```

### 2. Configure Environment

Create `.env` file:

```env
# Required
COHERE_API_KEY=your_cohere_api_key

# Optional (for specific features)
GITHUB_TOKEN=your_github_token
GITHUB_REPOSITORY=owner/repo
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TARGET_DB_URL=postgresql://user:pass@localhost:5432/db
```

### 3. Connect to IDE

Point to your local `server.py`:

```json
{
  "mcpServers": {
    "readiness-assistant": {
      "command": "python",
      "args": ["D:/path/to/mcp-ai-assistant/server.py"],
      "env": {
        "COHERE_API_KEY": "..."
      }
    }
  }
}
```

---

## 📚 Available Tools

### 🔍 Build & CI Tools

#### `get_latest_build`

**Automatically fetch and analyze the latest GitHub Actions build**

```
Args:
  repo (optional): Repository in "owner/repo" format. Defaults to GITHUB_REPOSITORY env var.
  workflow_name (optional): Filter by workflow name (e.g., "Next.js Build")
  branch (optional): Filter by branch (e.g., "main")
  include_log (optional): Fetch full logs (default: true)

Example:
  "Get my latest build"
  "Check the latest Next.js build on main branch"
```

**Returns**: Latest build status, conclusion, commit info, and AI-powered failure analysis with root cause and suggested fixes.

#### `fetch_build_log`

**Fetch logs for a specific build ID**

```
Args:
  build_id (required): GitHub Actions run ID
  repo (optional): Repository (defaults to GITHUB_REPOSITORY)

Example:
  "Fetch build log for run 12345"
```

#### `analyze_build_log`

**Analyze build logs with AI**

```
Args:
  log_text (required): Build log content

Example:
  "Analyze this build log: [paste log]"
```

---

### ⚙️ Configuration Tools

#### `compare_environment_configs`

**Detect configuration drift between environments**

```
Args:
  project (required): Project name
  env1 (required): First environment (e.g., "staging")
  env2 (required): Second environment (e.g., "production")

Example:
  "Compare staging and production configs for my-app"
```

**Supports**: JSON, YAML, .env, Java Properties, XML, Dockerfile ENV

**Returns**: Drift analysis with empty keys, mismatched values, and AI-powered explanations.

#### `fetch_environment_config`

**Fetch configuration for a single environment**

```
Args:
  project (required): Project name
  environment (required): Environment name

Example:
  "Fetch staging config for backend"
```

---

### 🏥 Health & Database Tools

#### `check_service_health`

**Check service endpoint health and latency**

```
Args:
  service_name (required): Service identifier
  health_url (required): Health check endpoint URL

Example:
  "Check health of https://api.example.com/health"
```

**Returns**: HTTP status, latency in ms, and AI assessment.

#### `check_database_connection`

**Test database connectivity and migrations**

```
Args:
  environment (required): Environment name

Example:
  "Check database connection for production"
```

**Supports**:

- PostgreSQL (asyncpg)
- MySQL (aiomysql)
- MongoDB (motor)

**Auto-detects** database type from `TARGET_DB_URL` connection string.

**Returns**: Connection status, latency, migration status, and AI recommendations.

---

### 📊 Orchestration Tools

#### `evaluate_build`

**Comprehensive deployment readiness audit**

```
Args:
  project (required): Project name
  build_id (required): Build ID to evaluate
  environment (required): Target environment

Example:
  "Evaluate build 12345 for production deployment"
```

**Performs**:

1. Fetches and analyzes build logs
2. Checks configuration drift
3. Validates service health
4. Calculates readiness score (0-100)

**Returns**: Full audit report with AI-generated executive summary.

#### `verify_build`

**Quick build verification (logs only)**

```
Args:
  project (required): Project name
  build_id (required): Build ID

Example:
  "Verify build 12345"
```

#### `verify_config`

**Quick config drift check**

```
Args:
  project (required): Project name
  environment (required): Environment

Example:
  "Verify config for staging"
```

#### `verify_health`

**Quick health check**

```
Args:
  project (required): Project name
  environment (required): Environment

Example:
  "Verify health for production"
```

---

## 🎯 Usage Examples

### Scenario 1: Check Latest Build

```
User: "What's the status of my latest build?"
Assistant: [Calls get_latest_build, shows AI analysis]
```

### Scenario 2: Full Deployment Audit

```
User: "Is build 12345 ready for production?"
Assistant: [Calls evaluate_build, provides comprehensive report]
```

### Scenario 3: Database Health Check

```
User: "Check if the production database is healthy"
Assistant: [Calls check_database_connection, shows latency and migration status]
```

### Scenario 4: Config Drift Detection

```
User: "Are staging and production configs in sync?"
Assistant: [Calls compare_environment_configs, highlights differences]
```

---

## 🔧 Configuration Schema

The server uses `readiness_schema.json` to define projects and environments:

```json
{
  "projects": {
    "my-app": {
      "repo": "owner/my-app",
      "environments": {
        "staging": {
          "config_path": "./config/staging.json",
          "services": [
            {
              "name": "api",
              "health_url": "https://staging-api.example.com/health"
            }
          ]
        },
        "production": {
          "config_path": "./config/production.json",
          "services": [
            {
              "name": "api",
              "health_url": "https://api.example.com/health"
            }
          ]
        }
      }
    }
  }
}
```

Initialize with:

```bash
python server.py --init-config
```

---

## 🌟 Key Features

### AI-First Architecture

- All diagnostics narrated by Cohere LLM
- Root cause identification for failures
- Actionable suggested fixes
- Context-aware explanations

### Multi-Database Support

- Auto-detects PostgreSQL, MySQL, MongoDB from connection string
- Async connectivity checks with real latency measurements
- Migration verification (Alembic for SQL, custom for MongoDB)

### Universal Config Parser

- Supports 6+ config formats
- Detects empty/invalid values
- Highlights drift across environments

### Robust Error Handling

- 60-second timeout with retry logic
- Exponential backoff for transient failures
- Graceful degradation with fallback responses

---

## 📦 Dependencies

- `mcp>=1.26.0` - MCP server framework
- `cohere` - AI-powered analysis (via requests to Cohere API)
- `asyncpg` - PostgreSQL async driver
- `aiomysql` - MySQL async driver
- `motor` - MongoDB async driver
- `pyyaml` - YAML parsing
- `requests` - HTTP client
- `python-dotenv` - Environment management

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

Built with ❤️ using:

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Cohere AI](https://cohere.com/)
- [GitHub Actions API](https://docs.github.com/en/rest/actions)
