from collections import Counter
from functools import lru_cache

import numpy as np
from faster_whisper import WhisperModel

from app.config import settings

SR = settings.sample_rate


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    return WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


def transcribe(audio: np.ndarray) -> tuple[str, str | None]:
    segments, info = get_model().transcribe(
        audio,
        language=settings.whisper_language or None,
        task="transcribe",
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=settings.initial_prompt or None,
    )
    text = " ".join(s.text.strip() for s in segments).strip()
    return text, info.language


def _tail_is_silent(audio: np.ndarray, seconds: float = 0.7, thresh: float = 0.01) -> bool:
    n = int(seconds * SR)
    if audio.size < n:
        return False
    return float(np.sqrt(np.mean(audio[-n:] ** 2))) < thresh


class StreamingSession:
    """Holds the audio of one WebSocket connection.

    Audio goes into `pcm` (int16 bytes). Every tick we transcribe the
    not-yet-committed audio and send it as a *partial*. When the speaker
    pauses (or the segment gets too long) we *commit* the text and start
    a fresh buffer, so each Whisper call stays short and fast.
    """

    def __init__(self) -> None:
        self.pcm = bytearray()
        self.committed: list[str] = []
        self.languages: Counter[str] = Counter()
        self.total_samples = 0
        self._processed_len = 0

    def add_pcm16(self, data: bytes) -> None:
        self.pcm.extend(data)
        self.total_samples += len(data) // 2

    def has_new_audio(self) -> bool:
        return len(self.pcm) > self._processed_len

    @property
    def duration(self) -> float:
        return self.total_samples / SR

    @property
    def full_text(self) -> str:
        return " ".join(self.committed).strip()

    @property
    def language_label(self) -> str | None:
        if not self.languages:
            return None
        return ", ".join(lang for lang, _ in self.languages.most_common(3))

    def step(self, final: bool = False) -> dict | None:
        n = len(self.pcm) - (len(self.pcm) % 2)  # snapshot, keep sample alignment
        self._processed_len = n
        audio = np.frombuffer(bytes(self.pcm[:n]), dtype=np.int16).astype(np.float32) / 32768.0
        seconds = audio.size / SR

        if seconds < settings.min_segment_sec and not final:
            return None
        if audio.size == 0:
            return None

        text, lang = transcribe(audio)

        commit = (
            final
            or seconds >= settings.max_segment_sec
            or (seconds >= 2.0 and _tail_is_silent(audio))
        )
        partial = text
        if commit:
            if text:
                self.committed.append(text)
                if lang:
                    self.languages[lang] += 1
            del self.pcm[:n]          # keep audio that arrived during transcription
            self._processed_len = 0
            partial = ""

        return {
            "type": "partial",
            "committed": self.full_text,
            "partial": partial,
            "language": lang,
        }
