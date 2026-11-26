from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://stt:stt@localhost:5432/stt"

    whisper_model: str = "small"          # tiny / base / small / medium
    whisper_device: str = "cpu"           # cpu / cuda
    whisper_compute_type: str = "int8"    # int8 for CPU, float16 for GPU
    whisper_language: str = ""            # "" = auto-detect

    # A Hinglish prompt nudges Whisper to write Hindi words in Roman script
    # and keep English words in English.
    initial_prompt: str = (
        "Namaste, aap kaise hain? I am doing good, chalo meeting start karte hain."
    )

    sample_rate: int = 16000
    partial_interval_sec: float = 1.5     # how often a partial result is sent
    max_segment_sec: float = 10.0         # force-commit a segment after this long
    min_segment_sec: float = 1.0          # don't transcribe less than this


settings = Settings()
