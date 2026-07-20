"""
MediSafe Eval Harness — LLM-as-judge + rule-based checks.

Run:
    python -m eval.eval
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from google import genai as google_genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from src.agents.orchestrator import create_orchestrator
from src.database.manager import init_db
from eval.test_cases import TEST_CASES

_APP_NAME = "MediSafe-Eval"
_USER_ID = "eval_user"
_JUDGE_MODEL = "gemini-3.5-flash"


async def _run_agent(
    runner: Runner, session_id: str, user_input: str
) -> tuple[str, list[str]]:
    """Run one turn and return (response_text, tools_called)."""
    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_input)],
    )
    final_response = ""
    tools_called = []

    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        # Capture every tool call across the whole agent tree
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    tools_called.append(part.function_call.name)

        # Capture the final text response
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response, tools_called


def _rule_checks(
    response: str, tools_called: list[str], tc: dict
) -> dict[str, bool]:
    results = {}
    for tool in tc.get("expected_tools", []):
        results[f"tool:{tool}"] = tool in tools_called
    for kw in tc.get("expected_keywords", []):
        results[f"keyword:{kw}"] = kw.lower() in response.lower()
    return results


def _llm_judge(user_input: str, response: str, rubric: str) -> bool:
    """Ask Gemini whether the response satisfies the rubric. Returns True = pass."""
    client = google_genai.Client()
    prompt = (
        f"You are evaluating an AI agent's response.\n\n"
        f"User asked: {user_input}\n"
        f"Agent responded: {response}\n\n"
        f"Rubric: {rubric}\n\n"
        f"Does the agent's response satisfy the rubric? Reply with only YES or NO."
    )
    result = client.models.generate_content(model=_JUDGE_MODEL, contents=prompt)
    return (result.text or "").strip().upper().startswith("YES")


def _print_report(results: list[dict]) -> None:
    passed = sum(1 for r in results if r["overall_pass"])
    total = len(results)

    print(f"\n{'=' * 56}")
    print(f"  MEDISAFE EVAL  —  {passed}/{total} passed")
    print(f"{'=' * 56}")

    categories: dict[str, list] = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    for cat, items in categories.items():
        cat_passed = sum(1 for i in items if i["overall_pass"])
        print(f"\n  [{cat.upper()}]  {cat_passed}/{len(items)}")
        for r in items:
            icon = "✓" if r["overall_pass"] else "✗"
            print(f"    {icon}  {r['id']}")
            for check, ok in r["rule_checks"].items():
                mark = "✓" if ok else "✗"
                print(f"          {mark}  {check}")
            judge_mark = "✓" if r["judge_pass"] else "✗"
            print(f"          {judge_mark}  llm-judge")
            if not r["overall_pass"]:
                preview = r["response"][:150].replace("\n", " ")
                print(f"          →  {preview}…")

    print()


async def _run() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_db = f.name

    # Point both the main process and the MCP subprocess at the temp DB
    os.environ["MEDISAFE_DB_PATH"] = tmp_db

    try:
        init_db()
        orchestrator, mcp_toolset = await create_orchestrator()
        session_service = InMemorySessionService()
        runner = Runner(
            agent=orchestrator,
            app_name=_APP_NAME,
            session_service=session_service,
        )

        results = []
        try:
            for tc in TEST_CASES:
                print(f"  {tc['id']} ...", end=" ", flush=True)

                # Fresh conversation context per test, but shared DB
                # so medications added in tc01 are visible in tc03+
                session = await session_service.create_session(
                    app_name=_APP_NAME, user_id=_USER_ID
                )

                response = ""
                tools_called: list[str] = []
                try:
                    response, tools_called = await _run_agent(
                        runner, session.id, tc["input"]
                    )
                    rule_checks = _rule_checks(response, tools_called, tc)
                    judge_pass = _llm_judge(tc["input"], response, tc["rubric"])
                    rules_pass = all(rule_checks.values()) if rule_checks else True
                    overall_pass = rules_pass and judge_pass
                except Exception as exc:
                    response = f"ERROR: {exc}"
                    rule_checks = {
                        **{f"tool:{t}": False for t in tc.get("expected_tools", [])},
                        **{f"keyword:{k}": False for k in tc.get("expected_keywords", [])},
                    }
                    judge_pass = False
                    overall_pass = False

                results.append({
                    "id": tc["id"],
                    "category": tc["category"],
                    "response": response,
                    "tools_called": tools_called,
                    "rule_checks": rule_checks,
                    "judge_pass": judge_pass,
                    "overall_pass": overall_pass,
                })
                print("PASS" if overall_pass else "FAIL")

        finally:
            await mcp_toolset.close()

        _print_report(results)

    finally:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
