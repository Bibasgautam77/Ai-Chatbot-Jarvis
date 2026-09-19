"""
Tools the assistant can actually invoke on your machine, exposed to Claude
via the Anthropic tool-use API. Claude decides when to call these based on
the conversation — you don't need to pattern-match user text yourself.

To add a new tool:
  1. Write a `run_<name>(**kwargs) -> str` function.
  2. Add its JSON schema to TOOL_SCHEMAS.
  3. Register it in TOOL_FUNCTIONS.
That's it — Claude will pick it up automatically.
"""

import datetime
import subprocess
import sys
import webbrowser

import memory


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def run_get_time(**kwargs) -> str:
    return datetime.datetime.now().strftime("%I:%M %p")


def run_get_date(**kwargs) -> str:
    return datetime.datetime.now().strftime("%A, %B %d, %Y")


def run_open_app(app: str, **kwargs) -> str:
    app_key = app.strip().lower()

    app_map_darwin = {
        "chrome": "Google Chrome", "notes": "Notes", "terminal": "Terminal",
        "vscode": "Visual Studio Code", "code": "Visual Studio Code",
        "spotify": "Spotify", "calculator": "Calculator",
    }
    app_map_windows = {
        "chrome": "chrome", "notepad": "notepad", "vscode": "code",
        "code": "code", "calculator": "calc", "spotify": "spotify",
    }
    app_map_linux = {
        "chrome": "google-chrome", "terminal": "x-terminal-emulator",
        "vscode": "code", "code": "code", "spotify": "spotify",
    }

    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-a", app_map_darwin.get(app_key, app)])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["start", "", app_map_windows.get(app_key, app)], shell=True)
        else:
            subprocess.Popen([app_map_linux.get(app_key, app)])
        return f"Opened {app}."
    except Exception as e:
        return f"Couldn't open {app}: {e}"


def run_web_search(query: str, **kwargs) -> str:
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Opened a search for '{query}' in the browser."


def run_open_url(url: str, **kwargs) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}."


def run_shell_command(command: str, **kwargs) -> str:
    """Runs a whitelisted-free shell command. Gated behind ALLOW_SHELL in
    config.py because arbitrary shell execution is genuinely dangerous —
    off by default."""
    from config import ALLOW_SHELL
    if not ALLOW_SHELL:
        return (
            "Shell command execution is disabled. Set ALLOW_SHELL = True "
            "in config.py if you understand the risk and want to enable it."
        )
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15
        )
        output = (result.stdout or result.stderr or "").strip()
        return output[:1000] if output else "Command ran with no output."
    except Exception as e:
        return f"Command failed: {e}"


def run_remember(fact: str, **kwargs) -> str:
    """Save a fact/preference so it's known in future sessions too, without
    the user repeating it."""
    return memory.add_fact(fact)


def run_teach_command(trigger: str, actions: list, **kwargs) -> str:
    """Save a taught macro: next time the user says `trigger`, replay
    `actions` (a list of {"tool": ..., "input": {...}}) directly -- no need
    to explain it again, and no LLM call needed to run it."""
    return memory.teach_macro(trigger, actions)


def run_list_taught_commands(**kwargs) -> str:
    return memory.list_macros()


def run_forget_everything(**kwargs) -> str:
    """Wipe all saved facts and taught commands. Only call this if the user
    clearly and explicitly asks to forget/reset everything."""
    return memory.forget_everything()


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "get_time",
        "description": "Get the current local time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_date",
        "description": "Get today's date.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_app",
        "description": "Open an application on the user's computer, e.g. Chrome, VS Code, Spotify, Terminal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app": {"type": "string", "description": "Name of the application to open."}
            },
            "required": ["app"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for a query, opening results in the default browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "open_url",
        "description": "Open a specific URL/website in the default browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to open."}
            },
            "required": ["url"],
        },
    },
    {
        "name": "run_shell_command",
        "description": (
            "Run a shell command on the user's machine. Disabled by default "
            "for safety — only use if the user has explicitly enabled it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run."}
            },
            "required": ["command"],
        },
    },
    {
        "name": "remember",
        "description": (
            "Save a fact or preference about the user so it's remembered in "
            "future sessions -- e.g. their name, preferred apps, timezone, "
            "or any standing preference they mention. Use this whenever the "
            "user tells you something worth not having to repeat."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The fact to remember, written plainly."}
            },
            "required": ["fact"],
        },
    },
    {
        "name": "teach_command",
        "description": (
            "Save a custom command the user is teaching you: a trigger phrase "
            "mapped to a fixed sequence of tool calls. Next time the user says "
            "the trigger phrase, you (or the fast-path matcher) will run these "
            "exact actions again WITHOUT the user re-explaining and without "
            "needing another AI call. Use this when the user says things like "
            "'remember this as X', 'next time I say Y, do Z', or 'teach you a command'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {
                    "type": "string",
                    "description": "The short phrase the user will say later to trigger this, e.g. 'start work mode'.",
                },
                "actions": {
                    "type": "array",
                    "description": "Sequence of tool calls to replay when triggered.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool": {
                                "type": "string",
                                "description": "Tool name: get_time, get_date, open_app, web_search, open_url, or run_shell_command.",
                            },
                            "input": {
                                "type": "object",
                                "description": "Input arguments for that tool, matching its schema.",
                            },
                        },
                        "required": ["tool", "input"],
                    },
                },
            },
            "required": ["trigger", "actions"],
        },
    },
    {
        "name": "list_taught_commands",
        "description": "List all custom commands the user has taught so far.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "forget_everything",
        "description": (
            "Wipe ALL remembered facts and taught commands. Only use this if "
            "the user explicitly and clearly asks to reset/forget everything "
            "-- this cannot be undone."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOL_FUNCTIONS = {
    "get_time": run_get_time,
    "get_date": run_get_date,
    "open_app": run_open_app,
    "web_search": run_web_search,
    "open_url": run_open_url,
    "run_shell_command": run_shell_command,
    "remember": run_remember,
    "teach_command": run_teach_command,
    "list_taught_commands": run_list_taught_commands,
    "forget_everything": run_forget_everything,
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(**tool_input)
    except Exception as e:
        return f"Tool '{name}' failed: {e}"
