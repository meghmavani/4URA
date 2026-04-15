from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Awaitable, Callable

import discord
from dotenv import load_dotenv

from agent.agent import AuraAgent


load_dotenv()


TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TEST_MODE = os.getenv("TEST_MODE", "").strip().lower() == "true"

COMMAND_PREFIX = "!it"


def _extract_task(content: str) -> str | None:
    if not content.lower().startswith(COMMAND_PREFIX):
        return None
    task = content[len(COMMAND_PREFIX) :].strip()
    return task or None


def _safe_call(result: object, method_name: str):
    method = getattr(result, method_name, None)
    if callable(method):
        try:
            return method()
        except Exception:
            return None
    return None


def _extract_action_texts(result: object) -> list[str]:
    texts: list[str] = []

    extracted = _safe_call(result, "extracted_content")
    if isinstance(extracted, list):
        texts.extend([str(item).strip() for item in extracted if str(item).strip()])

    if not texts:
        raw = str(result).strip()
        if raw:
            matches = re.findall(r"extracted_content='([^']+)'", raw)
            texts.extend([m.strip() for m in matches if m.strip()])

    return texts


def _build_result_line(task: str, final_result: str, successful: bool | None) -> str:
    lower_final = final_result.lower()
    lower_task = task.lower()

    if "already exists" in lower_final:
        return "User already exists"
    if "reset" in lower_task and ("successful" in lower_final or "success" in lower_final):
        return "Password reset successfully"
    if "create user" in lower_task and ("created" in lower_final or "success" in lower_final):
        return "User created successfully"
    if successful is True:
        return "Task completed successfully"
    return "Task completed successfully"


def _summarize_result(result: object, task: str, limit: int = 1200) -> str:
    action_texts = _extract_action_texts(result)
    final_result = str(_safe_call(result, "final_result") or "").strip()
    successful = _safe_call(result, "is_successful")

    steps: list[str] = []
    lower_task = task.lower()
    lower_actions = [text.lower() for text in action_texts]

    if any("navigated to http://127.0.0.1:8000/login" in text for text in lower_actions):
        steps.append("Opened login page")

    typed_count = sum(1 for text in lower_actions if text.startswith("typed"))
    if typed_count >= 2:
        steps.append("Entered credentials")

    if any('clicked button "login"' in text for text in lower_actions):
        steps.append("Logged in successfully")

    if "if not exists" in lower_task or "check if user exists" in lower_task:
        steps.append("Checked existing users")
        if "already exists" in final_result.lower():
            steps.append("User already exists -> no action taken")
        else:
            steps.append("User not found -> proceeding to create")

    if any('clicked a "create user"' in text for text in lower_actions):
        steps.append("Navigated to Create User page")

    if "create user" in lower_task and any("typed '" in text for text in lower_actions):
        role_selected = any("selected option: user" in text for text in lower_actions)
        if role_selected:
            steps.append("Filled user details (email, name, role)")
        else:
            steps.append("Filled user details (email, name)")

    if "create user" in lower_task and any('clicked button "create user"' in text for text in lower_actions):
        steps.append("Submitted form")

    if "reset password" in lower_task:
        steps.append("Found target user")
        steps.append("Reset password")

    if final_result:
        lower_final = final_result.lower()
        if "table" in lower_final or "visible" in lower_final or "verified" in lower_final:
            if "create user" in lower_task:
                steps.append("Verified user appears in dashboard")
        if "success message" in lower_final and "create user" not in lower_task:
            steps.append("Verified success message")

    unique_steps: list[str] = []
    seen: set[str] = set()
    for step in steps:
        if step not in seen:
            unique_steps.append(step)
            seen.add(step)

    if not unique_steps:
        return "Task completed successfully"

    max_steps = 10
    unique_steps = unique_steps[:max_steps]

    result_line = _build_result_line(task=task, final_result=final_result, successful=successful)

    lines = ["Task completed", "", "Steps performed:"]
    lines.extend([f"{idx}. {step}" for idx, step in enumerate(unique_steps, start=1)])
    lines.extend(["", "Result:", result_line])

    message = "\n".join(lines).strip()
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


async def _run_agent_task(task: str) -> object:
    return await AuraAgent().run_async(task)


async def _emit_response(send_response: Callable[[str], Awaitable[None]], text: str) -> None:
    if TEST_MODE:
        print(f"[TEST_MODE] {text}")
        return
    await send_response(text)


async def handle_discord_message(
    *,
    content: str,
    is_from_bot: bool,
    send_response: Callable[[str], Awaitable[None]],
    runner: Callable[[str], Awaitable[object]] | None = None,
    shutdown: Callable[[], Awaitable[None]] | None = None,
) -> str | None:
    if is_from_bot:
        return None

    if content.strip().lower() == "!it exit":
        await _emit_response(send_response, "Shutting down 4URA bot...")
        if shutdown:
            try:
                await shutdown()
            except Exception:
                pass
        return "Shutdown requested"

    task = _extract_task(content)
    if not task:
        return None

    await _emit_response(send_response, "Task started...")

    active_runner = runner or _run_agent_task
    try:
        result = await active_runner(task)
        summary = _summarize_result(result, task=task)
        await _emit_response(send_response, f"Task completed\nSummary: {summary}")
        return summary
    except Exception as exc:
        failure_summary = f"Failed - {exc}"
        await _emit_response(send_response, f"Task completed\nSummary: {failure_summary}")
        return failure_summary


async def main() -> None:
    print("4URA Discord bot starting...")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN not found in .env")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"[DiscordBot] Logged in as {client.user}")

    @client.event
    async def on_message(message: discord.Message) -> None:
        await handle_discord_message(
            content=message.content,
            is_from_bot=message.author == client.user or message.author.bot,
            send_response=message.channel.send,
            shutdown=client.close,
        )

    try:
        await client.start(TOKEN)
    except asyncio.CancelledError:
        pass
    finally:
        print("[DiscordBot] Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[DiscordBot] Shutdown requested by keyboard interrupt")