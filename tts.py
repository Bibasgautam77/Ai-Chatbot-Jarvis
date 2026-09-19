"""
Text-to-speech output. Uses pyttsx3 (fully offline, cross-platform:
Windows/SAPI5, macOS/NSSpeechSynthesizer, Linux/espeak).
"""

import threading
import pyttsx3

from config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX


class Speaker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", TTS_RATE)
        self.engine.setProperty("volume", TTS_VOLUME)

        voices = self.engine.getProperty("voices")
        if voices and 0 <= TTS_VOICE_INDEX < len(voices):
            self.engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)

        self._lock = threading.Lock()

    def say(self, text: str):
        """Speak text out loud (blocking)."""
        if not text:
            return
        print(f"\033[96mJarvis:\033[0m {text}")
        with self._lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def list_voices(self):
        """Utility: print available system voices with their index, so you
        can pick TTS_VOICE_INDEX in config.py."""
        for i, v in enumerate(self.engine.getProperty("voices")):
            print(f"[{i}] {v.name} ({v.id})")


if __name__ == "__main__":
    s = Speaker()
    s.list_voices()
    s.say("Hello, I am online.")
