import os
import requests
import platform
import subprocess
from murf import Murf

VOICE_MAP = {
    "en-US": ("en-US", "en-US-natalie"),
    "en-IN": ("en-IN", "en-IN-isha"),
    "en-UK": ("en-UK", "en-UK-theo"),
    "fr-FR": ("fr-FR", "fr-FR-axel"),
    "de-DE": ("de-DE", "de-DE-lia"),
    "es-ES": ("es-ES", "es-ES-carmen"),
    "it-IT": ("it-IT", "it-IT-lorenzo"),
    "pt-BR": ("pt-BR", "pt-BR-isadora"),
    "zh-CN": ("zh-CN", "zh-CN-tao"),
    "hi-IN": ("hi-IN", "hi-IN-shweta"),
    "ko-KR": ("ko-KR", "ko-KR-hwan"),
    "ta-IN": ("ta-IN", "ta-IN-iniya"),
    "pl-PL": ("pl-PL", "pl-PL-jacek"),
    "bn-IN": ("bn-IN", "bn-IN-ishani"),
    "ja-JP": ("ja-JP", "ja-JP-kenji"),
    "nl-NL": ("nl-NL", "nl-NL-dirk"),
    "hr-HR": ("hr-HR", "hr-HR-marija"),
    "el-GR": ("el-GR", "en-US-ken"),
    "ro-RO": ("ro-RO", "en-US-riley"),
    "sk-SK": ("sk-SK", "sk-SK-nina"),
}

def murf_translate(text: str, target_language: str) -> str:
    client = Murf(api_key=os.environ["MURF_API_KEY"])
    resp = client.text.translate(target_language=target_language, texts=[text])
    translations = getattr(resp, "translations", None)
    if translations and len(translations) > 0:
        return getattr(translations[0], "translated_text", "")
    return text

def text_to_speech_with_murf(text: str, filepath: str, voice_id: str):
    client = Murf(api_key=os.environ["MURF_API_KEY"])
    resp = client.text_to_speech.generate(text=text, voice_id=voice_id, format="wav")
    audio_url = getattr(resp, "audio_file", None) or getattr(resp, "audio_url", None)
    if not audio_url:
        raise ValueError("Audio URL not found in Murf response.")
    audio_data = requests.get(audio_url).content
    with open(filepath, "wb") as f:
        f.write(audio_data)

    os_name = platform.system()
    try:
        if os_name == "Darwin":
            subprocess.run(["afplay", filepath], check=False)
        elif os_name == "Windows":
            subprocess.run([
                "powershell", "-c",
                f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"
            ], check=False)
        else:
            subprocess.run(["aplay", filepath], check=False)
    except Exception as e:
        print(f"[Murf] Playback error: {e}")
