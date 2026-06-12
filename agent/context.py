SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use tools whenever they help you complete the task."
)


def create_context(task: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]


def trim_context(messages: list[dict], max_messages: int) -> list[dict]:
    if len(messages) <= max_messages:
        return messages
    system, user = messages[0], messages[1]
    rest = messages[2:]
    trimmed = rest[-(max_messages - 2):]
    return [system, user, *trimmed]
