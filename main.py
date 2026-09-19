"""
Jarvis-style personal assistant -- entry point.

Usage:
    python main.py            # text mode (type your messages)
    python main.py --voice    # voice mode (speak, and it speaks back)

Two layers of "not having to repeat yourself":
  1. FACTS: tell it something ("remember that I use VS Code") and it's
     saved to memory.json -- injected into every future session's context.
  2. MACROS: teach it a command ("next time I say 'start work', open Chrome
     and VS Code") and the SECOND time you say the trigger phrase, main.py
     catches it below and replays the saved actions directly -- no AI call,
     no re-explaining.

Voice mode uses a simple wake-word gate: say the wake word (default
"jarvis", set in config.py) to start listening for a command.
"""

import argparse

from config import ASSISTANT_NAME, WAKE_WORD
from brain import Brain
from tools import execute_tool
import memory

EXIT_PHRASES = {"exit", "quit", "goodbye", "stop", "shut down", "shutdown"}


def try_run_macro(user_text: str):
    """Check taught commands before touching the API at all.
    Returns a response string if a macro matched, else None."""
    match = memory.find_macro(user_text)
    if match is None:
        return None
    trigger, actions = match
    results = []
    for step in actions:
        result = execute_tool(step["tool"], step.get("input", {}))
        results.append(result)
    return " ".join(results) if results else f"Ran '{trigger}'."


def run_text_mode():
    print(f"{ASSISTANT_NAME} is online. Type 'exit' to quit.\n")
    brain = Brain()

    def announce_tool(name, tool_input):
        print(f"  \033[90m[using tool: {name}({tool_input})]\033[0m")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nShutting down.")
            break

        if not user_text:
            continue
        if user_text.lower() in EXIT_PHRASES:
            print(f"{ASSISTANT_NAME}: Goodbye.")
            break

        # Fast path: a previously-taught command, run instantly with no API call.
        macro_reply = try_run_macro(user_text)
        if macro_reply is not None:
            print(f"{ASSISTANT_NAME}: {macro_reply}")
            continue

        reply = brain.ask(user_text, on_tool_call=announce_tool)
        print(f"{ASSISTANT_NAME}: {reply}")


def run_voice_mode():
    # Imported lazily so text-mode users don't need mic/speaker deps installed.
    from stt import Listener
    from tts import Speaker

    listener = Listener()
    speaker = Speaker()
    brain = Brain()

    def announce_tool(name, tool_input):
        print(f"  [using tool: {name}({tool_input})]")

    speaker.say(f"{ASSISTANT_NAME} online. Say '{WAKE_WORD}' to wake me.")

    while True:
        heard = listener.listen_once(timeout=None, phrase_time_limit=6)
        if not heard:
            continue
        if WAKE_WORD not in heard.lower():
            continue

        speaker.say("Yes?")
        command_text = listener.listen_once(timeout=6, phrase_time_limit=10)
        if not command_text:
            speaker.say("I didn't catch that.")
            continue
        if command_text.lower().strip() in EXIT_PHRASES:
            speaker.say("Goodbye.")
            break

        macro_reply = try_run_macro(command_text)
        if macro_reply is not None:
            speaker.say(macro_reply)
            continue

        reply = brain.ask(command_text, on_tool_call=announce_tool)
        speaker.say(reply)


def main():
    parser = argparse.ArgumentParser(description=f"{ASSISTANT_NAME} personal assistant")
    parser.add_argument("--voice", action="store_true", help="Run in voice mode")
    args = parser.parse_args()

    if args.voice:
        run_voice_mode()
    else:
        run_text_mode()


if __name__ == "__main__":
    main()
