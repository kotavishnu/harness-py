SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use tools whenever they help you complete the task."
)


def create_context(task: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
