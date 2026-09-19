"""
The conversational "brain" -- sends user text + rolling history to Claude,
with tool-calling enabled. Claude decides when to call a tool (open an app,
check the time, search the web, etc.), we execute it locally, feed the
result back, and loop until Claude produces a final text answer.
"""

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, MODEL, SYSTEM_PROMPT, MAX_HISTORY_TURNS
from tools import TOOL_SCHEMAS, execute_tool
import memory


class Brain:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Run: export ANTHROPIC_API_KEY='sk-ant-...'"
            )
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history = []  # list of {"role": "user"|"assistant", "content": ...}

    def _system_prompt(self) -> str:
        # Pull in remembered facts fresh each call, so anything saved mid-session
        # (or by another run) is picked up without restarting.
        facts_block = memory.get_facts_text()
        if facts_block:
            return f"{SYSTEM_PROMPT}\n\n{facts_block}"
        return SYSTEM_PROMPT

    def ask(self, user_text: str, on_tool_call=None) -> str:
        """
        Send user_text to Claude, resolving any tool calls along the way.
        `on_tool_call(name, tool_input)` is an optional callback (e.g. to
        speak "Opening Chrome..." while it happens) fired before each tool runs.
        Returns the final text reply.
        """
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()

        # Loop: Claude may call one or more tools before giving a final answer.
        for _ in range(6):  # hard cap so a tool-call loop can't run forever
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=self._system_prompt(),
                tools=TOOL_SCHEMAS,
                messages=self.history,
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                # Final answer -- concatenate any text blocks.
                reply = "".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()
                self._trim_history()
                return reply

            # Handle every tool_use block in this turn, then send results back.
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if on_tool_call:
                    on_tool_call(block.name, block.input)
                result_text = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    }
                )

            self.history.append({"role": "user", "content": tool_results})

        return "I got stuck in a loop trying to handle that -- let's try something simpler."

    def _trim_history(self):
        # Keep only the last N turns (a "turn" = one user + one assistant msg)
        max_messages = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def reset(self):
        self.history = []


if __name__ == "__main__":
    brain = Brain()
    print(brain.ask("What time is it, and then open a search for weather today?"))
