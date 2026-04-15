from __future__ import annotations

import importlib

import pytest
from dotenv import load_dotenv

load_dotenv()

import bot


def test_extract_task_create_user_real_string() -> None:
    assert bot._extract_task("!it create user test@company.com") == "create user test@company.com"


def test_extract_task_reset_password_real_string() -> None:
    assert (
        bot._extract_task("!it reset password for test@company.com")
        == "reset password for test@company.com"
    )


@pytest.mark.asyncio
async def test_handle_discord_message_calls_aura_agent_run(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    class FakeAuraAgent:
        async def run_async(self, task: str) -> str:
            captured["task"] = task
            return "ok"

    async def fake_send(_: str) -> None:
        return None

    monkeypatch.setattr(bot, "AuraAgent", FakeAuraAgent)

    summary = await bot.handle_discord_message(
        content="!it create user test@company.com",
        is_from_bot=False,
        send_response=fake_send,
    )

    assert summary == "Task completed successfully"
    assert captured["task"] == "create user test@company.com"


@pytest.mark.asyncio
async def test_handle_discord_message_ignores_non_commands() -> None:
    sent: list[str] = []

    async def fake_send(text: str) -> None:
        sent.append(text)

    summary = await bot.handle_discord_message(
        content="hello there",
        is_from_bot=False,
        send_response=fake_send,
    )

    assert summary is None
    assert sent == []


@pytest.mark.asyncio
async def test_handle_discord_message_ignores_bot_messages() -> None:
    sent: list[str] = []

    async def fake_send(text: str) -> None:
        sent.append(text)

    summary = await bot.handle_discord_message(
        content="!it create user test@company.com",
        is_from_bot=True,
        send_response=fake_send,
    )

    assert summary is None
    assert sent == []


@pytest.mark.asyncio
async def test_exit_command_triggers_shutdown() -> None:
    sent: list[str] = []
    shutdown_called = False

    async def fake_send(text: str) -> None:
        sent.append(text)

    async def fake_shutdown() -> None:
        nonlocal shutdown_called
        shutdown_called = True

    summary = await bot.handle_discord_message(
        content="!it exit",
        is_from_bot=False,
        send_response=fake_send,
        shutdown=fake_shutdown,
    )

    assert summary == "Shutdown requested"
    assert shutdown_called is True
    assert sent == ["Shutting down 4URA bot..."]


@pytest.mark.asyncio
async def test_test_mode_logs_and_does_not_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_MODE", "true")
    reloaded_bot = importlib.reload(bot)

    sent: list[str] = []

    async def fake_send(text: str) -> None:
        sent.append(text)

    async def fake_runner(_: str) -> str:
        return "agent-result"

    summary = await reloaded_bot.handle_discord_message(
        content="!it reset password for test@company.com",
        is_from_bot=False,
        send_response=fake_send,
        runner=fake_runner,
    )

    assert summary is not None
    assert "Task completed" in summary
    assert "Result:" in summary
    assert "Task completed successfully" in summary
    assert sent == []
