from __future__ import annotations

import sys

from agent.agent import AuraAgent


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python main_agent.py \"create user john@company.com\"")
        print("   or: python main_agent.py \"reset password for john@company.com\"")
        return 1

    task = " ".join(sys.argv[1:]).strip()

    print(f"[Runner] Received task: {task}")
    agent = AuraAgent()
    result = agent.run(task)
    print("[Runner] Agent output:")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
