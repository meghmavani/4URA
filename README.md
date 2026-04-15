# 4URA — Automated User Request Agent

An AI-driven automation agent that interprets natural language IT requests and executes them via browser automation, integrated with Discord for seamless team communication.

---

## Overview

**4URA** (Automated User Request Agent) solves the problem of manual IT operations by enabling users to request common IT tasks in natural language:

- Instead of: *"Log in, navigate to the dashboard, click Create User, fill out the form..."*
- Just say: **`!it create user john@company.com`**

The agent understands your intent, plans the steps, and automates the entire workflow through the browser—no DOM selectors, no brittle automation code. Just AI-powered human-like interaction.

---

## Key Features

**Natural Language Understanding** — Parse complex IT requests without rigid syntax  
**Browser-Based Automation** — Use vision and reasoning instead of fragile selectors  
**Mock Admin Panel** — FastAPI + Jinja2 interface for user and credential management  
**Conditional Logic** — Handle "if not exists" and decision-tree workflows  
**Discord Integration** — Run tasks directly from Discord with formatted results  
**End-to-End Automation** — From user intent to completion in seconds  
**Full Test Coverage** — Unit, integration, and system tests (40+ passing)  

---
## 🚀 Live Demo

Try 4URA right now on Discord!

**Quick Start:**
1. **[Join the server](https://discord.gg/96tn6rXs)**
2. Click the **🔍 detective icon** to gain access to `#4ura`
3. Open the channel: [#4ura](https://discord.com/channels/864705058175713310/1493902176412631110)
4. Type your command: `!it <command>`

**Bot ID:** `1493899163077967973` (if running in DMs)

Example commands to try:
```
!it create user demo@company.com
!it reset password for alice@example.com
!it create user newuser@company.com if not exists
```

Watch the bot execute the full workflow in real-time and see results within seconds. 

---
## Demo Tasks

Run these commands in Discord after the bot is online:

```
!it create user john@company.com
!it reset password for alice@example.com
!it create user tolerant@company.com if not exists
!it exit (After tasks finish running, to gracefully stop execution)
```

The agent will execute them humanoid via the browser and report back with a summary of actions taken.

---

## How It Works

```
Discord Message
    ↓
  [Agent]
    ├─ Parse natural language
    ├─ Plan execution steps
    └─ Generate instructions
    ↓
  [Browser Automation]
    ├─ Launch headless Chrome
    ├─ Navigate with vision
    ├─ Fill forms, click buttons
    └─ Verify results
    ↓
  [Admin Panel]
    ├─ Login
    ├─ View/Modify users
    └─ Reset credentials
    ↓
  Discord Result Summary
```

### Components

- **Admin Panel** (`app/`) — FastAPI web interface for user management  
- **AuraAgent** (`agent/agent.py`) — LLM + browser-use orchestration  
- **Discord Bot** (`bot.py`) — Event handler and message processor  
- **Test Suite** (`tests/`) — Coverage for all major workflows

---

## Project Structure

```
4URA/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── static/
│   └── templates/
├── agent/
│   ├── __init__.py
│   └── agent.py
├── tests/
│   ├── test_app.py
│   ├── test_integration.py
│   ├── test_system.py
│   └── test_agent_features.py
├── bot.py
├── main_agent.py
├── requirements.txt
├── .env
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Chrome/Chromium browser (for automation)
- Discord account (for bot testing)
- OpenAI API key (GPT-4o model)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/meghmavani/4URA
   cd 4URA
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate it:**
   ```powershell
   .\.venv\Scripts\Activate.ps1

   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```
   OPENAI_API_KEY=sk-...
   DISCORD_BOT_TOKEN=MTE0OTM4OTkxNjMwNzc5Njc5NzMuRzYwSUEuMm5ucTJFNjlueW0yTzFfMElWRXNQSDlRRWdhSThySlVISDhYRWpRWXhqRTA
   TEST_MODE=false
   ```
   
   **Note:** The Discord bot token is pre-configured above. You can use it to run the bot locally and test with the [shared server](https://discord.gg/96tn6rXs). To use your own bot, replace with your token.
---

## Running the Project

### Full Stack (FastAPI + Discord Bot)

**Terminal 1 — Start the admin panel:**
```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser. Log in with any username/password.

**Terminal 2 — Start the Discord bot:**
```bash
python bot.py
```

The bot will connect to Discord. Send commands in a channel where the bot is present.

### CLI Only (No Discord)

Test the agent directly from the command line:

```bash
python main_agent.py "create user john@company.com"
```

This runs the browser automation and prints the result without requiring Discord.

---

## Testing

Run the full test suite:

```bash
pytest -v
```

**Test Categories:**
- **Unit tests** — Individual functions and classes
- **Integration tests** — Agent + Admin Panel workflows
- **System tests** — End-to-end task execution
- **Feature tests** — Discord message handling and bot commands

All tests pass in ~3 seconds and validate automation reliability.

---

## Design Decisions

### Why Browser Automation Over APIs?

We use **browser-use** (with GPT-4o vision) instead of direct API calls because:
- **Human-like interaction** — The agent sees what users see, not hidden API docs
- **Real-world workflow** — Tests exactly what users experience
- **No selectors** — Vision-based navigation is robust to UI changes
- **Generalizable** — Works with any web interface, not just custom APIs

### Why Mock Admin Panel?

A simplified web interface lets us:
- **Test end-to-end** without a real corporate environment
- **Focus on automation logic** rather than system integration
- **Scale quickly** for demos and evaluation
- **Control the UX** for reliable browser automation

### Why Discord Integration?

Discord provides:
- **Natural interface** for team communication
- **Familiar command syntax** (!it ...)
- **Async-safe execution** in an event-driven environment
- **Clear output formatting** for human readability

### Why Conditional Logic?

Requests like `create user if not exists` teach the agent:
- **Decision trees** (check → decide → act)
- **Error recovery** (user found → skip creation)
- **Practical workflows** (avoid duplicate users)

---

## Limitations

- **UI-dependent** — Layout changes require agent re-adaptation
- **Slower than API calls** — Browser automation takes ~15–30 seconds per task
- **Local server required** — Admin panel must be running
- **Vision-limited** — Accessibility text helps; pure images are harder to interpret
- **No persistent memory** — Agent doesn't learn across sessions

---

## Future Improvements

- **Real SaaS integration** — Connect to Slack, Jira, Okta, etc.
- **User roles & permissions** — Multi-tenant support with RBAC
- **Advanced UI understanding** — Multi-modal vision improvements
- **Voice commands** — Transcribe Discord voice messages
- **Performance tuning** — Parallel task execution  
- **Audit logging** — Track all automation actions for compliance

---

## Demo Video

[Loom Video: 4URA Live Automation](https://loom.com/share) ← Add link here after recording

---

## Troubleshooting

**Bot not responding?**
- Ensure bot token is correct in `.env`
- Confirm bot has message permissions in the channel
- Check that `python bot.py` is running

**Browser automation hangs?**
- Verify admin panel is running (`uvicorn app.main:app --reload`)
- Check that OpenAI API key is valid
- Ensure Chrome/Chromium is installed

**Tests failing?**
- Verify all dependencies installed: `pip install -r requirements.txt`
- Ensure admin panel is **not** running during test execution
- Run `pytest -v` for detailed output

---

## License

MIT

---

**Built with:** FastAPI, browser-use, discord.py, OpenAI GPT-4o, Playwright
