# 🤖 Sidekick - Your AI Assistant

A smart AI assistant that can search the web, send notifications, and save files - with built-in quality control.

## What It Does

- **Searches the web** for information (jobs, research, anything)
- **Sends push notifications** to your phone via Pushover
- **Saves results** to files automatically
- **Self-evaluates** its work and retries if needed
- **Remembers conversations** across sessions

![](https://github.com/lisekarimi/agentverse/blob/main/assets/mermaid_langgrah_sidekick.png?raw=true)

## Key Features

- **Worker Agent**: Does the actual task using tools
- **Evaluator Agent**: Judges quality and gives feedback
- **Self-improvement Loop**: Retries with feedback until success
- **Memory**: Persists conversations in SQLite database

## Setup

1. **Install dependencies** (`uv sync`)

2. **Create `.env` file** with your API keys:
```env
OPENAI_API_KEY=your-key-here
SERPER_API_KEY=your-serper-key
PUSHOVER_TOKEN=your-pushover-token
PUSHOVER_USER=your-pushover-user-key
```

## Run
```bash
cd 4_langgraph/sidekick
uv run app.py
```

That's it! Opens in your browser automatically.
