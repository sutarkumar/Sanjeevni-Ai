# ─────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────

import os
import base64
import traceback
import requests
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Custom modules for speech processing and TTS
from input_voice import transcribe_audio_and_detect_language
from output_voice import text_to_speech_with_murf, murf_translate, VOICE_MAP

# Load environment variables from .env file
load_dotenv()


# ─────────────────────────────────────────────────────────────
# CONFIGURATION CONSTANTS
# ─────────────────────────────────────────────────────────────

# URL of the React Avatar Frontend (for lip-sync + animation)
AVATAR_FRONTEND_URL = "http://localhost:5173"

# URL of the Node.js backend (handles lipsync + avatar playback)
NODE_BACKEND_URL = "http://localhost:3125"

# Mapping UI language selection → TTS language codes
LANGUAGE_MAP = {
    "English": "en-US",
    "Hindi":   "hi-IN",
}


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_target_lang(lang_label: str) -> str:
    """
    Convert UI language label into TTS language code.
    Default: Hindi (hi-IN)
    """
    return LANGUAGE_MAP.get(lang_label, "hi-IN")


def read_text_file(txt_file) -> str:
    """
    Read uploaded .txt file safely.
    Returns text content or empty string on failure.
    """
    if not txt_file:
        return ""
    try:
        path = txt_file.name if hasattr(txt_file, "name") else txt_file
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print("TXT read error:", e)
        return ""


def get_transcript(audio_path, txt_file):
    """
    Get user input from either:
    1. Uploaded text file
    2. Microphone audio

    Returns:
        (transcript, detected_language)
    """
    txt_content = read_text_file(txt_file)

    # If text file exists → priority
    if txt_content:
        return txt_content, "en"

    # Otherwise process audio
    if audio_path:
        try:
            transcript, detected_lang = transcribe_audio_and_detect_language(audio_path)
            return (transcript.strip() if transcript else ""), detected_lang
        except Exception as e:
            print("Transcription error:", e)
            traceback.print_exc()

    return "", "en"


def set_python_mode(active: bool):
    """
    Notify React avatar to enable/disable Python processing mode.
    Used to prevent conflicts during speech playback.
    """
    try:
        requests.post(
            f"{NODE_BACKEND_URL}/python-mode",
            json={"active": active},
            timeout=5,
        )
        print(f"🐍 python-mode → {active}")
    except Exception as e:
        print("set_python_mode error:", e)


# ─────────────────────────────────────────────────────────────
# PROMPT ENGINEERING
# ─────────────────────────────────────────────────────────────

def build_prompt(transcript: str, image_path=None) -> str:
    """
    Build a structured prompt for the LLM.
    Keeps response short and medical-style.
    """

    if transcript:
        return f"""
Doctor. Give VERY SHORT answer (max 1 line /each).

1. Cause:
2. Treatment:
3. Medicines: (no dose)

Symptoms: {transcript}
""".strip()

    elif image_path:
        return """
Doctor. VERY SHORT answer (1 line each).

1. Cause:
2. Treatment:
3. Medicines:
4. Home:

Guess only. See doctor.
""".strip()

    else:
        return """
Doctor.

1. Cause: Need details
2. Treatment: Describe symptoms
3. Medicines: Ask doctor
4. Home: Rest, water
""".strip()


# ─────────────────────────────────────────────────────────────
# LLM CALL (GROQ API)
# ─────────────────────────────────────────────────────────────

def call_groq(prompt: str) -> str:
    """
    Send prompt to Groq LLM and return response.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not found."

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )

        content = response.choices[0].message.content
        return content.strip() if content else "No response generated."

    except Exception as e:
        print("Groq API error:", e)
        traceback.print_exc()
        return f"Error: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TRANSLATION + TTS
# ─────────────────────────────────────────────────────────────

def translate_response(text: str, target_lang: str) -> str:
    """
    Translate LLM response into selected language (if required).
    """
    try:
        if target_lang.startswith("en"):
            return text

        translated = murf_translate(text, target_lang)
        return translated.strip() if translated else text

    except Exception as e:
        print("Translation error:", e)
        return text


def generate_tts_bytes(text: str, target_lang: str):
    """
    Convert text → speech (TTS) and return audio as bytes.
    Temporary file is deleted immediately.
    """
    try:
        _, voice_id = VOICE_MAP.get(target_lang, VOICE_MAP["en-US"])

        tmp_path = f"_tmp_tts_{target_lang}.wav"
        text_to_speech_with_murf(text, tmp_path, voice_id)

        if not os.path.exists(tmp_path):
            return None

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(tmp_path)  # Cleanup
        return audio_bytes

    except Exception as e:
        print("TTS error:", e)
        return None


# ─────────────────────────────────────────────────────────────
# AVATAR INTEGRATION
# ─────────────────────────────────────────────────────────────

def send_to_avatar(text: str, audio_bytes: bytes, mute=False) -> bool:
    """
    Send generated audio + lipsync data to avatar backend.
    Avatar will speak and animate accordingly.
    """
    if not audio_bytes:
        return False

    try:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Generate lip-sync data
        lip_res = requests.post(
            f"{NODE_BACKEND_URL}/lip-sync",
            json={"audioBase64": audio_b64},
            timeout=60,
        )

        lipsync = lip_res.json().get("lipsync", {"mouthCues": []}) if lip_res.ok else {"mouthCues": []}

        # Send to avatar player
        play_res = requests.post(
            f"{NODE_BACKEND_URL}/play-avatar",
            json={
                "text": text,
                "audio": audio_b64,
                "lipsync": lipsync,
                "facialExpression": "smile",
                "animation": "Talking_1",
                "mute": mute
            },
            timeout=30,
        )

        return play_res.ok

    except Exception as e:
        print("send_to_avatar error:", e)
        return False


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────

def process(audio_path, image_path, lang_label, txt_file):
    """
    Main pipeline:
    1. Get input (audio/text)
    2. Generate LLM response
    3. Translate
    4. Convert to speech
    5. Send to avatar
    6. Return results
    """
    try:
        set_python_mode(True)

        target_lang = get_target_lang(lang_label)

        transcript, _ = get_transcript(audio_path, txt_file)

        prompt = build_prompt(transcript, image_path)
        doctor_response = call_groq(prompt)

        doctor_response = translate_response(doctor_response, target_lang)

        audio_bytes = generate_tts_bytes(doctor_response, target_lang)

        if audio_bytes:
            send_to_avatar(doctor_response, audio_bytes, mute=True)

        txt_path = save_report(doctor_response)

        return transcript if transcript else "No input provided.", doctor_response, txt_path

    except Exception as e:
        traceback.print_exc()
        set_python_mode(False)

        error_msg = f"Unexpected error: {str(e)}"
        return "Error processing input.", error_msg, save_report(error_msg)
