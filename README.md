# MediSafe — AI Medication Management Concierge

> **Kaggle Capstone · Track: Concierge Agents**
> Google × Kaggle 5-Day AI Agents Intensive Vibe Coding Course (June 2026)

---

## What Is MediSafe?

Managing multiple medications is genuinely hard. Missed doses, unclear schedules, and undetected drug interactions are among the most common — and preventable — causes of medication-related harm. Yet most people rely on paper lists, phone alarms, or memory alone.

MediSafe is a conversational AI agent that acts as a personal medication concierge. You talk to it in plain English, and it handles the complexity:

- **"Add Lisinopril 10mg once daily at 8am"** → saved, encrypted, and tracked
- **"I just took my Metformin"** → dose recorded with timestamp
- **"How am I doing this week?"** → adherence report across all medications
- **"Is it safe to take Aspirin with Warfarin?"** → real-time interaction check from FDA data
- **"Tell me about Atorvastatin"** → pulls the official FDA drug label summary

All personal health data is **encrypted at rest**. MediSafe never shares, transmits, or logs your medication information. It runs entirely on your machine.

---

## What Problem Does It Solve?

| Problem | How MediSafe Helps |
|---|---|
| Forgetting to take medications | Conversational reminders; dose recording |
| Complicated multi-drug regimens | Single place to view all active medications and schedules |
| Dangerous drug-drug interactions | Real-time FDA interaction check before adding a new drug |
| Low adherence over time | Weekly/monthly adherence reports with encouragement |
| Not knowing what a drug does | Instant FDA label lookup in plain language |

---

## Who Is It For?

- People managing chronic conditions with multiple daily medications
- Caregivers tracking medications for elderly relatives
- Anyone who wants a private, local, AI-powered medication companion

---

## How It Works

MediSafe is built as a **multi-agent system** using the Google Agent Development Kit (ADK). Three AI agents work together behind a single conversational interface:

```
┌────────────────────────────────────────────────────────────────────┐
│                         You (chat)                                 │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│              MediSafe Orchestrator                                 │
│              (Google ADK · LlmAgent · Gemini)                      │
│                                                                    │
│  Understands your intent and routes to the right specialist.       │
│  Also has direct access to the medication database via MCP.        │
└──────────────┬────────────────────────────┬────────────────────────┘
               │ delegate                   │ delegate
               ▼                            ▼
┌──────────────────────────┐  ┌────────────────────────────────────┐
│  Medication Manager      │  │  Health Advisor                    │
│  (ADK · LlmAgent)        │  │  (ADK · LlmAgent)                  │
│                          │  │                                    │
│  • Add medications       │  │  • Check drug-drug interactions    │
│  • List active meds      │  │    using the OpenFDA public API    │
│  • Record doses taken    │  │  • Look up FDA drug label info     │
│  • Record skipped doses  │  │  • Explain warnings and purpose    │
│  • Adherence reports     │  └────────────────────────────────────┘
│  • Remove medications    │
└──────────────────────────┘
               │
               │ MCP stdio transport
               ▼
┌────────────────────────────────────────────────────────────────────┐
│              MediSafe MCP Server  (FastMCP)                        │
│                                                                    │
│  An MCP (Model Context Protocol) server that exposes the           │
│  medication database as structured tools. The orchestrator calls   │
│  these tools the same way it would call any external API.          │
│                                                                    │
│  Tools: add · list · mark taken · skip · remove · adherence        │
│         check interactions · drug info lookup                      │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│              SQLite Database  (~/.medisafe/medisafe.db)            │
│                                                                    │
│  medications table — name, dosage, frequency, schedule             │
│  doses table       — when each dose was taken or skipped           │
│                                                                    │
│  Sensitive fields (name, dosage, notes) are encrypted with         │
│  Fernet (AES-128-CBC + HMAC-SHA256) before being written.          │
│  The encryption key lives at ~/.medisafe/encryption.key            │
│  with file permissions 600 (owner read/write only).                │
└────────────────────────────────────────────────────────────────────┘
```

### The three agents and what they do

**Orchestrator** is the conversational front door. It reads your message, decides what kind of task it is, and either handles it directly or routes it to the right specialist. It also has direct access to the medication database via the MCP server for quick lookups.

**Medication Manager** is the scheduling specialist. It knows how to add and remove medications, record when you take or skip a dose, and calculate your adherence percentage over any time window. It is deliberately non-judgmental — if you missed doses, it encourages rather than shames.

**Health Advisor** is the safety specialist. It queries the OpenFDA public API to check whether two of your medications have documented interactions, and to retrieve what a drug is officially used for, what its warnings are, and how it should be taken. It always reminds you that it provides information, not medical advice.

### Why MCP?

The Model Context Protocol (MCP) decouples the AI agents from the data layer. The MCP server exposes the medication database as a set of typed tools that any MCP-compatible client can call — not just this agent. This means:

- The database logic is tested independently of the AI
- A future web UI, mobile app, or different agent framework could connect to the same MCP server without touching the AI code
- The agent cannot accidentally run arbitrary SQL — it can only call the defined tools

### Why encryption?

Medication data is personal health information. Storing it in plaintext in a SQLite file means anyone with access to your filesystem — another user, a backup service, a rogue application — could read your medication history. Fernet encryption ensures the stored values are unreadable without the key, which is itself stored with restrictive permissions.

---

## Course Concepts Demonstrated

This project satisfies the requirement to demonstrate **at least three** key concepts from the 5-Day AI Agents course:

| Concept | Where |
|---|---|
| **Multi-agent system (ADK)** | `src/agents/` — orchestrator delegates to two specialist sub-agents |
| **MCP Server** | `src/mcp_server/server.py` — FastMCP server with 8 tools over stdio transport |
| **Security features** | `src/security/encryption.py` — Fernet encryption for all PII; chmod 600 key file; parameterised SQL |

---

## Project Structure

```
medisafe-agent/
│
├── src/
│   ├── main.py                    Entry point — starts the chat interface
│   │
│   ├── agents/
│   │   ├── orchestrator.py        Root ADK agent; wires up MCP toolset and sub-agents
│   │   ├── medication_agent.py    Sub-agent: medication CRUD and dose tracking
│   │   └── health_agent.py        Sub-agent: drug interactions and FDA info
│   │
│   ├── mcp_server/
│   │   └── server.py              FastMCP server — 8 tools over stdio
│   │
│   ├── tools/
│   │   ├── medication_tools.py    Pure Python functions used by both the agent and MCP server
│   │   └── interaction_tools.py   OpenFDA API wrappers
│   │
│   ├── database/
│   │   └── manager.py             SQLite manager; all PII written through encryption layer
│   │
│   └── security/
│       └── encryption.py          Fernet encrypt/decrypt helpers; key lifecycle management
│
└── tests/
    ├── conftest.py                Fixtures: isolated temp DB and key for every test
    ├── test_encryption.py
    ├── test_database.py
    ├── test_medication_tools.py
    ├── test_interaction_tools.py
    ├── test_mcp_server.py
    └── test_agents.py             65 tests, 0 LLM calls made during testing
```

---

## Security Details

### What is encrypted

| Column | Encrypted |
|---|---|
| `medications.name_enc` | Yes — Fernet (AES-128-CBC + HMAC-SHA256) |
| `medications.dosage_enc` | Yes |
| `medications.notes_enc` | Yes |
| `medications.frequency` | No (non-identifying) |
| `doses.scheduled_date/time` | No (timestamps only) |

### What is never stored

MediSafe never asks for, stores, or transmits:
- Medical diagnoses or conditions
- Insurance or billing information
- Passwords or authentication credentials
- API keys (these live in `.env`, never in the database)

### SQL injection prevention

All database operations use parameterised queries. No user input is ever interpolated into a SQL string.

---

## Disclaimer

MediSafe is a scheduling and information tool. It does **not** provide medical advice. Drug interaction data comes from public FDA drug labels and may not be complete. Always consult your doctor or pharmacist before starting, changing, or stopping any medication.

---

## Local Setup & Running

See **[SETUP.md](SETUP.md)** for step-by-step installation and run instructions on macOS.

---

## License

MIT — see [LICENSE](../LICENSE)
