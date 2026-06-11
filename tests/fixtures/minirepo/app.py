from pathlib import Path


PROMPT_TEMPLATE = Path("prompts/agent_prompt.md")


class AgentRunner:
    def __init__(self, tools: dict[str, str]) -> None:
        self.tools = tools
        self.history: list[str] = []

    def load_prompt(self) -> str:
        return PROMPT_TEMPLATE.read_text(encoding="utf-8")

    def plan_task(self, task: str) -> list[str]:
        self.history.append(task)
        if "summarize" in task:
            return ["read", "summarize"]
        return ["read", "answer"]

    def execute_tool(self, name: str) -> str:
        return self.tools.get(name, "missing")

    def remember(self, note: str) -> None:
        self.history.append(f"note:{note}")


def run(task: str) -> str:
    runner = AgentRunner({"read": "context", "answer": "done", "summarize": "brief"})
    runner.remember("started")
    steps = runner.plan_task(task)
    return " -> ".join(runner.execute_tool(step) for step in steps)
