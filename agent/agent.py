from __future__ import annotations

import asyncio
import inspect
import os
import re
from typing import Any


class AuraAgent:
    def __init__(self) -> None:
        try:
            from browser_use import Agent as BrowserUseAgent
            from browser_use.browser.profile import BrowserProfile
            from browser_use.browser.session import BrowserSession
            from browser_use.llm.openai.chat import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependencies. Run 'pip install -r requirements.txt' first."
            ) from exc

        print("[AuraAgent] Using OpenAI GPT-4o via browser-use ChatOpenAI")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self._agent_class = BrowserUseAgent
        self._browser_profile_class = BrowserProfile
        self._browser_session_class = BrowserSession

    def _build_browser_session(self) -> Any:
        launch_args = [
            "--disable-extensions",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu",
        ]
        headless = os.getenv("AURA_HEADLESS", "false").strip().lower() == "true"

        browser_profile = self._browser_profile_class(
            headless=headless,
            args=launch_args,
            is_local=True,
            use_cloud=False,
            enable_default_extensions=False,
            keep_alive=False,
            user_data_dir=None,
            storage_state=None,
        )

        return self._browser_session_class(
            browser_profile=browser_profile,
            is_local=True,
            use_cloud=False,
            cloud_browser=False,
            keep_alive=False,
            enable_default_extensions=False,
            headless=headless,
            args=launch_args,
        )

    def run(self, task: str):
        print(f"[AuraAgent] Starting task: {task}")
        return asyncio.run(self._run(task))

    async def run_async(self, task: str):
        print(f"[AuraAgent] Starting task: {task}")
        return await self._run(task)

    async def _run(self, task: str):
        instruction = self._task_to_instruction(task)

        print("[AuraAgent] Running with OpenAI...")
        agent_kwargs: dict[str, Any] = {"task": instruction, "llm": self.llm}
        browser_session = self._build_browser_session()

        supported = set(inspect.signature(self._agent_class).parameters.keys())

        if "browser_session" in supported:
            agent_kwargs["browser_session"] = browser_session

        optional_speed_config: dict[str, Any] = {
            "max_steps": int(os.getenv("AURA_MAX_STEPS", "22")),
            "retry_delay": float(os.getenv("AURA_RETRY_DELAY_SECONDS", "1.5")),
            "step_timeout": float(os.getenv("AURA_STEP_TIMEOUT_SECONDS", "22")),
            "max_failures": int(os.getenv("AURA_MAX_FAILURES", "3")),
            "planning_replan_on_stall": int(os.getenv("AURA_REPLAN_ON_STALL", "1")),
            "final_response_after_failure": False,
        }
        for key, value in optional_speed_config.items():
            if key in supported:
                agent_kwargs[key] = value

        agent: Any = self._agent_class(**agent_kwargs)
        result = await agent.run()
        print("[AuraAgent] Task finished")
        return result

    def _task_to_instruction(self, task: str) -> str:
        cleaned = task.strip()
        lower = cleaned.lower()

        if lower.startswith("create user "):
            remainder = cleaned[len("create user ") :].strip()
            remainder_lower = remainder.lower()

            if_not_exists = "if not exists" in remainder_lower
            if if_not_exists:
                marker_index = remainder_lower.index("if not exists")
                email = remainder[:marker_index].strip()
            else:
                email = remainder

            return self._build_create_user_instruction(email, conditional=if_not_exists)

        if "check if user exists" in lower:
            email = self._extract_email(cleaned)
            return self._build_create_user_instruction(email, conditional=True)

        if lower.startswith("reset password for "):
            email = cleaned[len("reset password for ") :].strip()
            return self._build_reset_password_instruction(email)

        raise ValueError(
            "Unsupported task. Use 'create user <email>', 'create user <email> if not exists', "
            "'check if user exists <email>', or 'reset password for <email>'"
        )

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if not match:
            raise ValueError("Could not find an email address in the task.")
        return match.group(0)

    def _build_create_user_instruction(self, email: str, conditional: bool = False) -> str:
        name = email.split("@")[0].replace(".", " ").replace("_", " ").title() or "New User"
        safe_navigation = (
            "Navigate to http://127.0.0.1:8000/login and wait briefly if needed before interacting. "
        )

        if conditional:
            return (
                "Perform the task reliably. "
                "Wait briefly if the page has not updated. "
                + safe_navigation
                + "Then sign in and land on the dashboard table. "
                f"Target email: '{email}'. "
                "Scan the table once and list visible emails, then compare with the target. "
                "If target exists: do not create a user and output exactly 'User already exists'. "
                f"If target is missing: click Create User, submit email '{email}' and name '{name}' (role User if available), "
                "verify success and table row, then output exactly 'User created successfully'."
            )

        return (
            "Perform the task reliably. "
            "Wait briefly if the page has not updated. "
            + safe_navigation
            + "Then sign in, go to Create User, "
            f"submit email '{email}' and name '{name}' (role User if available), then verify success and the new table row."
        )

    def _build_reset_password_instruction(self, email: str) -> str:
        safe_navigation = (
            "Navigate to http://127.0.0.1:8000/login and wait briefly if needed before interacting. "
        )
        return (
            "Perform the task reliably. "
            "Wait briefly if the page has not updated. "
            + safe_navigation
            + "Then sign in and find email "
            f"'{email}' in the table. If missing, state user does not exist and stop. "
            "If found, click Reset Password and verify success message."
        )
