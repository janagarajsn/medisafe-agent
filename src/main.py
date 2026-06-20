"""MediSafe — entry point

Run the interactive CLI agent:
    python -m src.main
or:
    python src/main.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Validate API key early so the user gets a clear error
if not os.environ.get("GOOGLE_API_KEY"):
    sys.exit(
        "\n[MediSafe] ERROR: GOOGLE_API_KEY is not set.\n"
        "Copy .env.example → .env and add your key from https://aistudio.google.com/app/apikey\n"
    )

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from src.agents.orchestrator import create_orchestrator
from src.database.manager import init_db

_APP_NAME = "MediSafe"
_USER_ID = os.environ.get("MEDISAFE_USER_ID", "default_user")

_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║     MediSafe — AI Medication Management Concierge            ║
║     Powered by Google ADK + Gemini                           ║
║     Your health data is encrypted at rest  🔒                ║
╚══════════════════════════════════════════════════════════════╝
Type 'help' for example commands, or 'quit' / 'exit' to leave.
"""


def _print_help() -> None:
    print(
        "\nExample prompts:\n"
        "  • Add Lisinopril 10mg once daily at 8am\n"
        "  • Add Metformin 500mg twice a day at 8am and 8pm\n"
        "  • Show my medications\n"
        "  • I just took my Lisinopril\n"
        "  • Show my adherence for the last 7 days\n"
        "  • Check interactions between Warfarin and Aspirin\n"
        "  • Tell me about Metformin\n"
        "  • Remove medication ID 3\n"
    )


async def _run() -> None:
    init_db()
    print(_BANNER)

    orchestrator, mcp_toolset = await create_orchestrator()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=orchestrator,
        app_name=_APP_NAME,
        session_service=session_service,
    )
    session = await session_service.create_session(app_name=_APP_NAME, user_id=_USER_ID)

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nMediSafe: Goodbye! Stay healthy!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print("MediSafe: Goodbye! Remember to take your medications on time!")
                break
            if user_input.lower() == "help":
                _print_help()
                continue

            message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_input)],
            )

            print("MediSafe: ", end="", flush=True)
            async for event in runner.run_async(
                user_id=_USER_ID,
                session_id=session.id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(part.text, end="")
            print("\n")
    finally:
        await mcp_toolset.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
