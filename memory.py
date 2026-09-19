"""
Persistent memory, stored as plain JSON right next to the script.
This is what makes the assistant "remember" things between runs instead of
forgetting everything the moment you close the terminal.

Two kinds of memory:
  - facts: short pieces of info the user told it to remember
           ("my name is Ravi", "I prefer VS Code over Notepad")
  - macros: taught commands -- a trigger phrase mapped to a fixed sequence
            of tool calls, so the SECOND time you say the trigger, it just
            replays the actions instantly, without asking Claude again.
"""

import json
import os
import threading

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")

_lock = threading.Lock()


def _default_memory():
    return {"facts": [], "macros": {}}


def load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return _default_memory()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("facts", [])
            data.setdefault("macros", {})
            return data
    except (json.JSONDecodeError, OSError):
        return _default_memory()


def save_memory(data: dict):
    with _lock:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def add_fact(fact: str) -> str:
    data = load_memory()
    if fact not in data["facts"]:
        data["facts"].append(fact)
        save_memory(data)
        return f"Got it, I'll remember: {fact}"
    return "I already knew that."


def get_facts_text() -> str:
    """Rendered as a block to inject into the system prompt so Claude has
    this context every session, without you repeating it."""
    data = load_memory()
    if not data["facts"]:
        return ""
    bullet_list = "\n".join(f"- {f}" for f in data["facts"])
    return f"Known information about the user (remembered from earlier sessions):\n{bullet_list}"


def teach_macro(trigger: str, actions: list) -> str:
    data = load_memory()
    data["macros"][trigger.strip().lower()] = actions
    save_memory(data)
    return f"Learned it. Next time you say '{trigger}', I'll do that automatically."


def find_macro(user_text: str):
    """Returns (trigger, actions) if user_text matches a taught macro
    (exact match or the trigger phrase is contained in what was said),
    else None."""
    data = load_memory()
    text = user_text.strip().lower()
    if text in data["macros"]:
        return text, data["macros"][text]
    for trigger, actions in data["macros"].items():
        if trigger in text:
            return trigger, actions
    return None


def list_macros() -> str:
    data = load_memory()
    if not data["macros"]:
        return "No custom commands taught yet."
    lines = [f"- '{trigger}'" for trigger in data["macros"]]
    return "Taught commands:\n" + "\n".join(lines)


def forget_everything() -> str:
    save_memory(_default_memory())
    return "Memory wiped -- facts and taught commands are gone."
