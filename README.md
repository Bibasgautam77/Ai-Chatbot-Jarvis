# Jarvis — a complete local AI assistant with memory

A local Python assistant with two modes:
- **Text mode**: type messages, get replies in your terminal.
- **Voice mode**: say a wake word, speak your request, hear a spoken reply.

It uses real **tool-calling** (Claude decides when to check the time, open
an app, search the web, etc.) plus **persistent memory**, so you don't have
to re-explain things every session.

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Entry point — text mode or `--voice` mode; also the macro fast-path |
| `brain.py` | Talks to Claude, runs the tool-calling loop, injects remembered facts |
| `tools.py` | Capabilities: time, apps, web search, URLs, shell, remember, teach_command |
| `memory.py` | Persistent storage (`memory.json`) for facts and taught macros |
| `stt.py` | Microphone → text (Google Web Speech API) |
| `tts.py` | Text → speech (offline, via `pyttsx3`) |
| `config.py` | Settings: name, wake word, model, voice, safety switches |
| `setup.bat` | Windows: one-time install (venv + dependencies) |
| `run_jarvis.bat` | Windows: double-click to start in text mode |
| `run_jarvis_voice.bat` | Windows: double-click to start in voice mode |

## Windows quick start (using the .bat files)

1. Install Python from https://python.org — during install, **check "Add
   Python to PATH"**.
2. Double-click **`setup.bat`** once. This creates a virtual environment and
   installs everything needed.
3. Set your API key (one time, in a terminal):
   ```
   setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
   ```
   Then close and reopen any terminal (or just double-click the .bat files
   below — they run in a fresh process that picks up the new key).
4. Double-click **`run_jarvis.bat`** to chat by typing, or
   **`run_jarvis_voice.bat`** to talk to it out loud.

That's it — no typing commands in a terminal required after setup.

## macOS / Linux quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py            # text mode
python main.py --voice    # voice mode
```

`PyAudio` (needed for voice mode) requires PortAudio first:
- **macOS**: `brew install portaudio` then `pip install pyaudio`
- **Ubuntu/Debian**: `sudo apt-get install python3-pyaudio portaudio19-dev`
  and `sudo apt-get install espeak` for offline TTS

Text mode alone only needs the `anthropic` package — skip audio setup if you
just want to type.

## The two kinds of memory — "so I don't have to say it again"

### 1. Facts (things it just knows from now on)

Just tell it something naturally:

> "Remember that I use VS Code, not Notepad."
> "My name is Ravi, remember that."

Claude calls the `remember` tool, which saves it to `memory.json`. Every
future session (even after closing and reopening) automatically includes
these facts in its context — you never repeat them.

### 2. Taught commands / macros (do X when I say Y)

This is the one that answers "second time I shouldn't have to say it
again" directly. Teach it once:

> "Next time I say 'start work', open Chrome and open VS Code."
> "Teach a command: when I say 'good night', close everything and search
> for tomorrow's weather."

Claude calls `teach_command`, saving a trigger phrase + the exact sequence
of actions to `memory.json`. **The second time** you say the trigger
phrase, `main.py` catches it *before* even calling the AI — it just replays
the saved actions instantly. That means:
- No AI call needed (faster, free)
- No need to re-explain what you want
- Works identically in text or voice mode

Say "list my commands" (or just ask) and Claude will call
`list_taught_commands` to show you what's been taught.

To wipe everything and start fresh, delete `memory.json` (or ask it to
forget everything — that maps to `run_shell_command`-free reset logic you
can wire up in `memory.forget_everything()` if you want a dedicated tool
for it).

## What it can do out of the box

- `get_time` / `get_date`
- `open_app` — opens applications by name (cross-platform mapping included)
- `web_search` — opens a Google search in your browser
- `open_url` — opens a specific website
- `run_shell_command` — **disabled by default**; flip `ALLOW_SHELL = True`
  in `config.py` only if you understand the risk
- `remember` — save a fact for future sessions
- `teach_command` — save a trigger phrase + action sequence as a macro
- `list_taught_commands` — show what's been taught so far

## Add your own tools

Open `tools.py`. Each tool is:
1. A `run_<name>(**kwargs) -> str` function that does the work.
2. A JSON schema entry in `TOOL_SCHEMAS` describing it to Claude.
3. A registration in `TOOL_FUNCTIONS`.

Claude — and the macro system, since macros just call these same tools —
will pick it up automatically.

## Customize personality & voice

Everything tunable lives in `config.py`:
- `ASSISTANT_NAME` / `WAKE_WORD`
- `MODEL` — swap Claude models
- `SYSTEM_PROMPT` — personality and tone
- `TTS_RATE`, `TTS_VOLUME`, `TTS_VOICE_INDEX` (run `python tts.py` to list
  available system voices and their index)

## Security note

`run_shell_command` is real code execution and is off by default on
purpose. Only enable it in a trusted, personal environment. Also review
`memory.json` occasionally — since Claude can write facts and macros to it
via tool calls, it's worth glancing at what's been saved there.
