"""
Central configuration for the assistant.
Edit these values (or set them as environment variables) to customize behavior.
"""

import os

# --- Identity ---
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
WAKE_WORD = os.getenv("WAKE_WORD", "jarvis").lower()  # only used in voice mode

# --- Anthropic API ---
# Set this in your shell: export ANTHROPIC_API_KEY="sk-ant-..."
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("JARVIS_MODEL", "claude-sonnet-4-6")

# --- Voice settings ---
TTS_RATE = int(os.getenv("TTS_RATE", "175"))       # words per minute
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "1.0")) # 0.0 - 1.0
TTS_VOICE_INDEX = int(os.getenv("TTS_VOICE_INDEX", "0"))  # index into system voices list

# --- Behavior ---
SYSTEM_PROMPT = (
    f"You are {ASSISTANT_NAME}, a concise, capable personal assistant running locally "
    "on the user's computer, in the style of a witty but efficient AI butler. "
    "Keep spoken responses short (1-3 sentences) unless asked for detail. "
    "You have tools to check the time/date, open apps, search the web, open URLs, "
    "and (if enabled) run shell commands. Use them when they'd actually help instead "
    "of just describing what you would do. If you have no tool for something, say so "
    "plainly rather than pretending to do it."
)

# Shell command execution is a real security risk (arbitrary code execution
# on request). Leave this False unless you understand and accept that.
ALLOW_SHELL = False

# How many turns of conversation history to keep in memory
MAX_HISTORY_TURNS = 20
