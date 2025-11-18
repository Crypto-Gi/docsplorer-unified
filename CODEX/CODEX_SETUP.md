# Codex + Docsplorer MCP Setup Guide

This guide shows you, step by step, how to:

1. Install a **Codex** client that supports MCP.
2. Connect Codex to the **Docsplorer MCP server** in this repo.
3. Make Codex use your **agent system prompt** in `CODEX/AGENTS.md`.

It is written for complete beginners.

> **Note:** I could not fetch the external `mcp://exa` documentation resource, so this guide uses standard MCP patterns. Always cross-check with the official Codex docs for any UI-specific steps.

---

## 1. What You Need First

Before you start:

- This repository cloned:
  - `git clone https://github.com/Crypto-Gi/docsplorer-unified.git`
- Docker and Docker Compose installed **OR** Python 3.11+ installed.
- A Codex client that supports **MCP servers** (HTTP or stdio).

You do **not** need to understand all the code. You just need to follow the commands and copy/paste some paths.

---

## 2. Start the Docsplorer MCP Stack

You have two main options: **Docker Compose** (recommended) or **local Python**.

### Option A: Run via Docker Compose (Recommended)

From the repo root:

```bash
cd docsplorer-unified
cp .env.example .env   # if you have not done this yet
# Edit .env to set QDRANT_DEV_URL, OLLAMA_HOST, etc.

# Start both services (Search API + MCP server)
docker compose up
```

This will start:

- **Search API**: `http://localhost:${SEARCH_API_PORT}` (default 8001)
- **MCP HTTP Server**: `http://localhost:${MCP_HTTP_PORT}/mcp` (default 8505)

You should see logs like:

```text
Docsplorer MCP Server
Mode: HTTP server on 0.0.0.0:8505
HTTP MCP endpoint (for tools like n8n, HTTP clients, etc.):
  URL: http://localhost:8505/mcp
```

Leave this terminal running.

### Option B: Run MCP Server via Python (stdio or HTTP)

From the repo root:

```bash
cd services/mcp-server
pip install -r requirements.txt
```

#### Stdio Mode (for MCP over stdio)

```bash
python server.py
```

This runs the MCP server in **stdio** mode (reads from stdin, writes to stdout). Codex (if it supports stdio MCP) will spawn this command directly.

#### HTTP Mode (direct, without Docker)

```bash
python server.py --transport http --host 0.0.0.0 --port 8505
```

The HTTP endpoint will be:

```text
http://localhost:8505/mcp
```

---

## 3. Make Codex Use Your AGENTS.md System Prompt

You created:

- `CODEX/AGENTS.md` – this is the **system prompt** that defines how the agent should behave.

Open `CODEX/AGENTS.md` and review it. It contains:

- Core identity and purpose.
- Hard guardrails (no hallucinations, evidence-based RAG only).
- Workflow phases.
- Validation matrix.
- Response format.

In Codex, you will usually have one of these UI patterns:

- A field called **System Prompt** or **Instruction**.
- A way to **load from file**.

### Basic approach

1. Open `CODEX/AGENTS.md` in your editor.
2. Copy the entire contents.
3. In Codex, go to the configuration for the assistant/agent:
   - Paste the text into the **System Prompt** or **Agent Instructions** field.
4. Save the configuration/profile.

Some Codex clients also support referencing a prompt file; if so, point it to:

```text
/path/to/your/checkout/docsplorer-unified/CODEX/AGENTS.md
```

(Adjust the path to match your machine.)

---

## 4. Configure Codex to Use the Docsplorer MCP Server

Codex must know how to reach your MCP server. Typically, you configure **one MCP server entry**.

There are two general connection styles:

### 4.1 HTTP MCP Connection

Use this when you run the MCP server in HTTP mode (via Docker Compose or Python `--transport http`).

In Codex, you typically configure the MCP server via a config file at:

```bash
~/.codex/config.toml
```

Add a section like this (adjust the IP/URL to match your machine):

```toml
[mcp_servers.docsplorer]
url = "http://192.168.254.22:8505/mcp"
startup_timeout_sec = 30
tool_timeout_sec = 60
```

Notes:

- Change `192.168.254.22` to your own host IP, or `localhost` if Codex runs on the same machine as the MCP server.
- You can change the table name `docsplorer` if you prefer another label.

If Codex also exposes a UI for MCP servers, it will mirror the same settings:

- **Name**: `docsplorer`
- **Type**: HTTP MCP server
- **URL**: `http://your-ip-or-localhost:8505/mcp`

If Codex asks for headers:

- Normally you can leave them empty unless you secure the MCP server.
- If you add auth later, set the header accordingly (e.g., `Authorization: Bearer ...`).

### 4.2 stdio MCP Connection

Use this when you run the MCP server as a local process spawned by Codex.

In Codex, configure an MCP server with:

- **Name**: `docsplorer`
- **Type**: stdio MCP
- **Command**:

  ```text
  python
  ```

- **Arguments**:

  ```text
  /path/to/your/checkout/docsplorer-unified/services/mcp-server/server.py
  ```

- **Working directory** (if required):

  ```text
  /path/to/your/checkout/docsplorer-unified/services/mcp-server
  ```

Codex will then launch the MCP server and communicate via stdio.

> Exact UI labels will depend on the Codex client you use, but the idea is always:
> - HTTP: URL = `http://localhost:8505/mcp`
> - stdio: Command = `python server.py`

---

## 5. How Codex Uses the Docsplorer Tools

Once connected, Codex will see tools from the Docsplorer MCP server, such as:

- `search_filenames_fuzzy`
- `search_with_filename_filter`
- `search_multi_query_with_filter`
- `search_across_multiple_files`
- `compare_versions`

You do **not** need to call these directly with curl when using Codex. Instead:

1. Start a conversation with Codex.
2. Tell it what you want, in natural language, for example:
   - "List all ECOS 9.2 release notes you can see."
   - "In ECOS 9.2.11.1 release notes, what DHCP changes were made?"
   - "Compare DHCP-related fixes between ECOS 9.2.11.1 and 9.3.7.0."
3. The agent (using `AGENTS.md` rules) will:
   - Use `search_filenames_fuzzy` to discover files.
   - Pick filenames.
   - Use `search_with_filename_filter` / `compare_versions` to retrieve content.
   - Return answers **with citations**.

If you want to see exactly what the server is doing, you can watch the MCP logs:

```bash
# In another terminal
cd /home/mir/projects/docsplorer-unified
docker compose logs -f mcp-server
```

---

## 6. End-to-End Checklist for Newcomers

If you are new and just want to make this work, follow this exact sequence:

1. **Clone the repo**:

   ```bash
   git clone https://github.com/Crypto-Gi/docsplorer-unified.git
   cd docsplorer-unified
   ```

2. **Set up `.env`**:

   ```bash
   cp .env.example .env
   # edit .env and set:
   #   QDRANT_DEV_URL
   #   OLLAMA_HOST
   #   OLLAMA_EMBEDDING_MODEL
   #   etc.
   ```

3. **Start the stack** (Search API + MCP):

   ```bash
   docker compose up
   ```

4. **Open Codex** and add a new MCP server:
   - Type: HTTP MCP server
   - URL: `http://localhost:8505/mcp`

5. **Set the system prompt**:
   - Open `CODEX/AGENTS.md`
   - Copy all contents
   - Paste into Codex's System Prompt / Agent Instructions field for this assistant.

6. **Test it**:
   - Ask: "Find all ECOS 9.2 release notes you know about and show filenames with citation pages."
   - Confirm that:
     - Docsplorer tools are being used (see logs).
     - Answers contain citations (filenames and page numbers).

If something fails, check:

- `docker compose logs search-api`
- `docker compose logs mcp-server`
- That Codex MCP configuration points to the right URL / command.

---

## 7. Notes About Codex Installation

Because the `mcp://exa` documentation resource could not be loaded, this guide cannot provide exact installation commands for your specific Codex client.

However, the usual pattern is:

1. Go to the official Codex website or docs.
2. Download the installer for your OS (Windows, macOS, Linux).
3. Install and log in if required.
4. Open settings/preferences.
5. Look for **MCP Servers** or **Tools / Integrations** section.
6. Add the Docsplorer MCP configuration as described above.

Once Codex is installed and configured, all MCP-specific behavior (which tools to call, how to display them) is handled by Codex itself.

---

## 8. Summary

- `CODEX/AGENTS.md` defines how the Docsplorer agent thinks and answers.
- The MCP server exposes search tools over HTTP (`/mcp`) or stdio.
- Codex connects to the MCP server and lets the agent call those tools.
- You interact in plain English; the agent handles all tool calls under the hood.

With this setup, a new user can:

- Install Codex.
- Clone this repo.
- Start the Docker stack.
- Paste in the system prompt.
- Immediately start asking deep questions about ECOS release notes and other docs, with strictly citation-backed answers.
