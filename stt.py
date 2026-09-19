"""
Speech-to-text input via microphone, using the `speech_recognition` library.
Uses Google's free web speech API by default (needs internet, no key required
for light usage). Swap `recognize_google` for `recognize_whisper` if you want
a fully offline option (requires `openai-whisper` + ffmpeg installed).
"""

import speech_recognition as sr


class Listener:
    def __init__(self, energy_threshold: int = 300, pause_threshold: float = 0.8):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.mic = sr.Microphone()

        # Calibrate for ambient noise once at startup
        with self.mic as source:
            print("Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen_once(self, timeout: float = 5, phrase_time_limit: float = 10) -> str:
        """Listen for a single utterance and return the transcribed text.
        Returns "" if nothing was understood or on timeout."""
        with self.mic as source:
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                return ""

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"\033[93mYou said:\033[0m {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[STT] Speech service error: {e}")
            return ""


if __name__ == "__main__":
    listener = Listener()
    print("Say something...")
    print("Heard:", listener.listen_once())
