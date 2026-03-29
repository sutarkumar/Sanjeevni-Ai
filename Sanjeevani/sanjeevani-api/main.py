# sanjeevani-api/main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import base64
import sys
import shutil
import time
from dotenv import load_dotenv

load_dotenv()

# ====================== PATH FIX ======================
current_dir = os.path.dirname(os.path.abspath(__file__))
sanjeevaani_folder = os.path.abspath(os.path.join(current_dir, "..", "..", "Sanjeevani"))
sys.path.insert(0, sanjeevaani_folder)

print(f"✅ Sanjeevaani folder path added: {sanjeevaani_folder}")

# ====================== IMPORTS ======================
try:
    from input_voice import transcribe_audio_and_detect_language
    from output_voice import text_to_speech_with_murf, murf_translate, VOICE_MAP
    print("✅ Successfully imported input_voice and output_voice!")
except Exception as e:
    print("❌ Import Error:", e)
    raise

app = FastAPI(title="Sanjeevani AI Doctor API")

# ================== CORS FIX (Important) ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_doctor_prompt(transcript: str) -> str:
    return f"""You are an experienced medical doctor. Provide a clear, structured response in simple language.
Do not say you are an AI.

Use exactly this format:

1. Possible Disease/Condition: ...
2. Why It May Have Happened: ...
3. How It Can Be Treated: ...
4. Medicines Usually Given: ... (no exact dosage)
5. Home Remedies: ...
6. What Can Happen If Ignored: ...

Symptoms: {transcript}

Keep it practical and easy to understand."""

# ====================== TRANSCRIBE (Fixed) ======================
@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    temp_path = f"temp_{int(time.time())}.wav"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Simple version without conversion (for testing)
        transcript, detected_lang = transcribe_audio_and_detect_language(temp_path)
        
        return {"transcript": transcript.strip(), "language": detected_lang}

    except Exception as e:
        print("Transcribe Error:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


# ====================== DIAGNOSE ======================
@app.post("/diagnose")
async def diagnose(
    transcript: str = Form(...),
    target_language: str = Form("hi-IN")
):
    try:
        prompt = get_doctor_prompt(transcript)
        
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        doctor_text = (response.choices[0].message.content or "").strip()

        if target_language.split("-")[0] != "en":
            try:
                doctor_text = murf_translate(doctor_text, target_language)
            except:
                pass

        return {"doctor_text": doctor_text, "target_language": target_language}

    except Exception as e:
        print("Diagnose Error:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


# ====================== SPEAK ======================
@app.post("/speak")
async def speak(
    text: str = Form(...),
    language: str = Form("hi-IN")
):
    try:
        _, voice_id = VOICE_MAP.get(language, VOICE_MAP["en-US"])
        output_file = f"temp_response_{int(time.time())}.wav"

        text_to_speech_with_murf(text, output_file, voice_id)

        with open(output_file, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        if os.path.exists(output_file):
            os.remove(output_file)

        return {"text": text, "audio_base64": audio_base64}

    except Exception as e:
        print("Speak Error:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    print("🚀 Sanjeevani API starting on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)