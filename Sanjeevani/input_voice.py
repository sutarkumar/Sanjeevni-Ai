import os
import logging
from io import BytesIO
from typing import Optional

import speech_recognition as sr
from pydub import AudioSegment
from groq import Groq
from langdetect import detect
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STT_MODEL = "whisper-large-v3"

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

def record_audio(
    file_path: str,
    timeout: int = 20,
    phrase_time_limit: Optional[int] = None
) -> None:
    """Record from the default microphone and save as WAV."""
    rec = sr.Recognizer()

    with sr.Microphone() as src:
        logging.info("Adjusting for ambient noise...")
        rec.adjust_for_ambient_noise(src, duration=1)
        logging.info("Please speak now...")
        audio = rec.listen(
            src,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit
        )

    wav = audio.get_wav_data()
    seg = AudioSegment.from_wav(BytesIO(wav))
    seg.export(file_path, format="wav")
    logging.info(f"Saved recording to {file_path}")

def transcribe_audio_and_detect_language(audio_filepath: str) -> tuple[str, str]:
    """Return (transcript, lang_code) using Groq STT + langdetect."""
    client = Groq(api_key=GROQ_API_KEY)

    with open(audio_filepath, "rb") as fd:
        result = client.audio.transcriptions.create(
            model=STT_MODEL,
            file=fd
        )

    text = (result.text or "").strip()

    if not text:
        logging.warning("No text transcribed from audio.")
        return "", "unknown"

    try:
        lang = detect(text)
    except Exception:
        lang = "unknown"

    logging.info(f"Transcribed '{text}' (lang: {lang})")
    return text, lang

