# MediSafe — Local Setup Guide

This guide walks you through everything needed to run MediSafe on a MacBook from scratch.

---

## Prerequisites

Before you start, make sure you have:

| Requirement | Check command | Minimum version |
|---|---|---|
| macOS | — | Ventura 13+ |
| Python | `python3 --version` | 3.11 or higher |
| pip | `pip3 --version` | bundled with Python |
| Internet access | — | needed for Gemini API + OpenFDA |

---

## Step 1 — Get a Google API Key

MediSafe uses Gemini as its AI model. You need a free API key.

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key — you will need it in Step 4

> The free tier of the Gemini API is sufficient to run this project.

---

## Step 2 — Install Python (if needed)

Check your Python version first:

```bash
python3 --version
```

If you have **Python 3.11 or higher**, skip to Step 3.

If you need to install or upgrade Python, use Homebrew:

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Verify
python3.12 --version
```

---

## Step 3 — Clone the Repository and Navigate to the Project

```bash
git clone https://github.com/your-username/medisafe-agent.git
cd medisafe-agent
```

If you already have the repository cloned, just navigate to the project folder:

```bash
cd /path/to/medisafe-agent
```

---

## Step 4 — Create a Virtual Environment

A virtual environment keeps MediSafe's dependencies isolated from the rest of your system.

```bash
# Create the virtual environment (only need to do this once)
python3 -m venv .venv

# Activate it (do this every time you open a new terminal)
source .venv/bin/activate
```

Your terminal prompt will now start with `(.venv)` to confirm it is active.

> **Every time you open a new terminal window to work on this project, run `source .venv/bin/activate` again.**

---

## Step 5 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all required packages including Google ADK, the MCP SDK, the encryption library, and the test framework. It takes about 1–2 minutes.

To confirm everything installed correctly:

```bash
python -c "import google.adk; import mcp; import cryptography; print('All dependencies OK')"
```

---

## Step 6 — Configure Your API Key

```bash
# Copy the example config file
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder with your actual key:

```
GOOGLE_API_KEY=AIzaSy...your_actual_key_here...
```

Save the file. The `.env` file is listed in `.gitignore` and will not be committed to version control.

---

## Step 7 — Run the Agent

```bash
python -m src.main
```

You should see:

```
╔══════════════════════════════════════════════════════════════╗
║     MediSafe — AI Medication Management Concierge            ║
║     Powered by Google ADK + Gemini                           ║
║     Your health data is encrypted at rest  🔒                ║
╚══════════════════════════════════════════════════════════════╝
Type 'help' for example commands, or 'quit' / 'exit' to leave.

You:
```

You are now talking to the agent. Type `help` to see example prompts.

---

## Example Prompts to Try

Once the agent is running, try these in order:

```
# Add medications
Add Lisinopril 10mg once daily at 8am
Add Metformin 500mg twice a day at 8am and 8pm
Add Atorvastatin 20mg once daily at bedtime

# View your medications
Show my medications

# Record doses
I just took my Lisinopril
I took my Metformin this morning
I skipped my evening Metformin

# Check how you are doing
Show my adherence for the last 7 days

# Look up drug safety information
Check interactions between Warfarin and Aspirin
Tell me about Metformin
What is Lisinopril used for?

# Remove a medication (use the ID shown in the list)
Remove medication ID 3

# Get help or quit
help
quit
```

---

## How to Stop the Agent

Type `quit` or `exit` at the prompt, or press `Ctrl+C`.

---

## Running the Tests

The test suite runs 65 tests without making any real API calls or modifying your data.

```bash
# Make sure your virtual environment is active
source .venv/bin/activate

# Run all tests
pytest -v
```

To run a specific test file:

```bash
pytest tests/test_encryption.py -v
pytest tests/test_database.py -v
pytest tests/test_medication_tools.py -v
pytest tests/test_mcp_server.py -v
pytest tests/test_agents.py -v
```

A passing run looks like:

```
======================== 65 passed in 0.88s ========================
```

---

## Where Your Data Is Stored

MediSafe stores everything locally on your machine — nothing is sent to any external server:

| File | What it contains |
|---|---|
| `~/.medisafe/medisafe.db` | Your medications and dose history (sensitive fields encrypted) |
| `~/.medisafe/encryption.key` | The encryption key (permissions: 600, owner-only) |

To completely remove all stored data:

```bash
rm -rf ~/.medisafe
```

> This permanently deletes your medication history and encryption key. There is no recovery — the encrypted database cannot be read without the key.

---

## Understanding What Runs When

When you type `python -m src.main`, here is what happens:

```
python -m src.main
  │
  ├── Initialises the SQLite database (creates ~/.medisafe/ if needed)
  ├── Starts the Google ADK Runner with the Orchestrator agent
  ├── Spawns python src/mcp_server/server.py as a background subprocess
  │     (this is the MCP server — it starts and stops automatically)
  └── Opens the interactive chat loop
```

**You only ever run `python -m src.main`.** The MCP server is managed automatically — you should never need to start it separately.

---

## Troubleshooting

**`GOOGLE_API_KEY is not set`**

You have not created a `.env` file or the key is missing from it. Run:
```bash
cp .env.example .env
# then edit .env and add your key
```

**`ModuleNotFoundError`**

Your virtual environment is not active. Run:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**`(.venv)` is missing from my prompt**

The virtual environment is not active. Run `source .venv/bin/activate` from the root directory.

**Agent gives a generic error or no response**

Your API key may be invalid or over quota. Check [aistudio.google.com](https://aistudio.google.com) to verify the key is valid and the free quota has not been exhausted.

**`InvalidToken` error on startup**

The encryption key file may be corrupted. Deleting `~/.medisafe/` will reset everything (all stored medications will be lost):
```bash
rm -rf ~/.medisafe
python -m src.main
```

**Tests fail with `OperationalError`**

Make sure you are running pytest from inside the root directory:
```bash
cd /path/to/medisafe-agent
pytest -v
```

---

## Quick Reference

```bash
# First-time setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add GOOGLE_API_KEY to .env

# Every time you return to the project
source .venv/bin/activate
python -m src.main

# Run tests
pytest -v
```
