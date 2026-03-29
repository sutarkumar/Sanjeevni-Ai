import os
import base64
import traceback
import requests
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

from input_voice import transcribe_audio_and_detect_language
from output_voice import text_to_speech_with_murf, murf_translate, VOICE_MAP

load_dotenv()

AVATAR_FRONTEND_URL = "http://localhost:5173"
NODE_BACKEND_URL    = "http://localhost:3125"

LANGUAGE_MAP = {
    "English": "en-US",
    "Hindi":   "hi-IN",
}

CUSTOM_CSS = """
body, .gradio-container {
    background: linear-gradient(135deg, #0f172a 0%, #111827 35%, #1e293b 100%) !important;
    color: #ffffff !important;
    font-family: 'Segoe UI', sans-serif;
}
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
    padding-top: 20px !important;
    padding-bottom: 30px !important;
}
.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 8px;
    background: linear-gradient(90deg, #60a5fa, #22d3ee, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sub-title {
    text-align: center;
    font-size: 16px;
    color: #cbd5e1;
    margin-bottom: 24px;
}
.glass-card {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 22px !important;
    padding: 18px !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
}
.section-heading {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 14px;
    color: #f8fafc;
}
.section-note {
    font-size: 14px;
    color: #cbd5e1;
    margin-bottom: 18px;
}
.avatar-frame {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
    background: rgba(255,255,255,0.04);
}
.footer-text {
    text-align: center;
    font-size: 13px;
    color: #94a3b8;
    margin-top: 18px;
}
button.primary-btn {
    background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(59, 130, 246, 0.35) !important;
}
button.primary-btn:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
    transition: 0.2s ease;
}
textarea, input, .gr-textbox, .gr-audio, .gr-file, .gr-image, .gr-dropdown {
    border-radius: 14px !important;
}
label {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_target_lang(lang_label: str) -> str:
    return LANGUAGE_MAP.get(lang_label, "hi-IN")


def read_text_file(txt_file) -> str:
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
    txt_content = read_text_file(txt_file)
    if txt_content:
        return txt_content, "en"
    if audio_path:
        try:
            transcript, detected_lang = transcribe_audio_and_detect_language(audio_path)
            return (transcript.strip() if transcript else ""), detected_lang
        except Exception as e:
            print("Transcription error:", e)
            traceback.print_exc()
    return "", "en"


def set_python_mode(active: bool):
    try:
        requests.post(
            f"{NODE_BACKEND_URL}/python-mode",
            json={"active": active},
            timeout=5,
        )
        print(f"🐍 python-mode → {active}")
    except Exception as e:
        print("set_python_mode error:", e)




def build_prompt(transcript: str, image_path=None) -> str:
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

def call_groq(prompt: str) -> str:
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


def translate_response(text: str, target_lang: str) -> str:
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
    Generate TTS audio and return as raw bytes.
    Temp file is deleted immediately — Gradio never sees a filepath.
    """
    try:
        _, voice_id = VOICE_MAP.get(target_lang, VOICE_MAP["en-US"])
        tmp_path = f"_tmp_tts_{target_lang}.wav"
        text_to_speech_with_murf(text, tmp_path, voice_id)

        if not os.path.exists(tmp_path):
            return None

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(tmp_path)   # ✅ Delete immediately
        return audio_bytes
    except Exception as e:
        print("TTS error:", e)
        return None

def send_to_avatar(text: str, audio_bytes: bytes, mute=False) -> bool:
    if not audio_bytes:
        return False
    try:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Lipsync
        lip_res = requests.post(
            f"{NODE_BACKEND_URL}/lip-sync",
            json={"audioBase64": audio_b64},
            timeout=60,
        )
        if lip_res.ok:
            lipsync = lip_res.json().get("lipsync", {"mouthCues": []})
        else:
            lipsync = {"mouthCues": []}

        # 🔥 ADD mute FLAG HERE
        play_res = requests.post(
            f"{NODE_BACKEND_URL}/play-avatar",
            json={
                "text": text,
                "audio": audio_b64,
                "lipsync": lipsync,
                "facialExpression": "smile",
                "animation": "Talking_1",
                "mute": mute   # 🔥 IMPORTANT
            },
            timeout=30,
        )

        return play_res.ok

    except Exception as e:
        print("send_to_avatar error:", e)
        return False


def save_report(text: str) -> str:
    txt_path = "doctor_advice.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print("Report save error:", e)
    return txt_path


# ─────────────────────────────────────────────────────────────────────────────
# MIC STOP
# ─────────────────────────────────────────────────────────────────────────────

def on_audio_recorded(audio_path):
    if not audio_path:
        return ""
    try:
        transcript, _ = transcribe_audio_and_detect_language(audio_path)
        transcript = transcript.strip() if transcript else ""
        if transcript:
            print(f"🎙 Mic transcript: '{transcript}'")
            try:
                requests.post(
                    f"{NODE_BACKEND_URL}/set-transcript",
                    json={"transcript": transcript},
                    timeout=5,
                )
            except Exception:
                pass
        return transcript
    except Exception as e:
        print("on_audio_recorded error:", e)
        traceback.print_exc()
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PROCESS
# ─────────────────────────────────────────────────────────────────────────────

def process(audio_path, image_path, lang_label, txt_file):
    try:
        # 1. Mute React
        set_python_mode(True)

        target_lang = get_target_lang(lang_label)

        # 2. Transcript
        transcript, _ = get_transcript(audio_path, txt_file)

        # 3. LLM
        prompt          = build_prompt(transcript, image_path)
        doctor_response = call_groq(prompt)

        # 4. Translate
        doctor_response = translate_response(doctor_response, target_lang)

        # 5. TTS → bytes only, no file path anywhere
        audio_bytes = generate_tts_bytes(doctor_response, target_lang)

        # 6. Send to avatar (lipsync + audio)
        if audio_bytes:
            send_to_avatar(doctor_response, audio_bytes, mute=True)

        # 7. Save report
        txt_path = save_report(doctor_response)

        final_transcript = transcript if transcript else "No speech/text provided."

        # 8. Unmute React after payload delivered
        # import time
        # # time.sleep(2)
        # set_python_mode(False)

        # ✅ Only 3 return values — out_audio is NOT in outputs list
        return final_transcript, doctor_response, txt_path

    except Exception as e:
        traceback.print_exc()
        set_python_mode(False)
        error_msg = f"Unexpected error: {str(e)}"
        return "Error processing input.", error_msg, save_report(error_msg)


# ─────────────────────────────────────────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Sanjeevani AI Doctor", css=CUSTOM_CSS) as demo:

    gr.HTML("""
        <div class="main-title">🌍 Sanjeevani - AI Doctor with 3D Avatar</div>
        <div class="sub-title">
            Smart AI medical guidance with voice input, multilingual response, and a talking 3D doctor avatar
        </div>
    """)

    with gr.Row():

        # ── LEFT ─────────────────────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🩺 Patient Input</div>')
            gr.HTML('<div class="section-note">Speak your concern, upload a report text file, or add an optional medical image.</div>')

            mic = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎙️ Speak your concern",
            )
            img = gr.Image(
                type="filepath",
                label="📷 Upload medical image (optional)",
            )
            txt = gr.File(
                label="📄 Or upload symptoms .txt",
                file_types=[".txt"],
            )
            lang = gr.Dropdown(
                choices=["English", "Hindi"],
                value="Hindi",
                label="🌐 Response Language",
            )
            submit = gr.Button("🧑‍⚕️ Get Diagnosis", elem_classes="primary-btn")
            gr.HTML('</div>')

        # ── RIGHT ─────────────────────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🧑‍⚕️ 3D Talking Doctor Avatar</div>')
            gr.HTML('<div class="section-note">Your AI doctor will speak the generated response through the connected avatar system.</div>')

            gr.HTML(f"""
                <div class="avatar-frame">
                    <iframe
                        id="react-avatar-frame"
                        src="{AVATAR_FRONTEND_URL}"
                        width="100%"
                        height="650"
                        style="border:none;"
                        allow="autoplay; microphone; camera">
                    </iframe>
                </div>
                <script>
                (function () {{
                    const LOCK_MS = 600, POLL_MS = 200, MAX_POLLS = 60;
                    let iframe = null, gradioBtn = null, locked = false, polls = 0;

                    const lock = () => {{ locked = true; setTimeout(() => locked = false, LOCK_MS); }};
                    const tellReact = (msg) => {{ if (iframe?.contentWindow) iframe.contentWindow.postMessage(msg, "*"); }};

                    const findGradioBtn = () => (
                        document.querySelector('button[aria-label="Record audio"]') ||
                        document.querySelector('button[aria-label="Stop recording"]') ||
                        document.querySelector('button[aria-label="Pause recording"]') ||
                        [...document.querySelectorAll("button")].find(b =>
                            /record|stop recording/i.test(b.getAttribute("aria-label") || "") ||
                            /record/i.test(b.innerText || ""))
                    );

                    const gradioIsRecording = () => {{
                        const lbl = (gradioBtn?.getAttribute("aria-label") || "").toLowerCase();
                        return lbl.includes("stop") || lbl.includes("pause");
                    }};

                    const onGradioBtnClick = () => {{
                        if (locked) return;
                        lock();
                        tellReact(gradioIsRecording() ? "GRADIO_RCD_STOP" : "GRADIO_RCD_START");
                    }};

                    window.addEventListener("message", (e) => {{
                        if (!["REACT_RCD_START","REACT_RCD_STOP"].includes(e.data) || locked) return;
                        if ((e.data === "REACT_RCD_START") !== gradioIsRecording() && gradioBtn) {{
                            lock(); gradioBtn.click();
                        }}
                    }});

                    const wire = (btn) => {{
                        if (gradioBtn) gradioBtn.removeEventListener("click", onGradioBtnClick, true);
                        gradioBtn = btn;
                        gradioBtn.addEventListener("click", onGradioBtnClick, true);
                    }};

                    const poller = setInterval(() => {{
                        polls++;
                        if (!iframe) iframe = document.getElementById("react-avatar-frame");
                        const btn = findGradioBtn();
                        if (btn && btn !== gradioBtn) wire(btn);
                        if (iframe && gradioBtn) {{ clearInterval(poller); console.log("[Bridge] ✅ Ready"); }}
                        else if (polls >= MAX_POLLS) {{ clearInterval(poller); console.warn("[Bridge] ⚠ Timeout"); }}
                    }}, POLL_MS);

                    new MutationObserver(() => {{
                        const btn = findGradioBtn();
                        if (btn && btn !== gradioBtn) wire(btn);
                    }}).observe(document.body, {{ childList: true, subtree: true }});
                }})();
                </script>
            """)
            gr.HTML('</div>')

    gr.HTML("<br>")

    with gr.Row():
        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">📝 Transcription</div>')
            out_transcript = gr.Textbox(
                label="Detected Symptoms / Input Text",
                lines=4,
                placeholder="Your speech or uploaded text will appear here...",
            )
            gr.HTML('</div>')

        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">💬 Doctor Response</div>')
            out_response = gr.Textbox(
                label="Doctor's Advice",
                lines=12,
                placeholder="Generated medical guidance will appear here...",
            )
            gr.HTML('</div>')

    gr.HTML("<br>")

    with gr.Row():
        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🎭 Voice Output</div>')
            gr.HTML('<div style="color:#94a3b8;font-size:14px;padding:12px 0;">Doctor is speaking via the 3D avatar on the right →</div>')
            gr.HTML('</div>')

        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">📄 Download Report</div>')
            out_file = gr.File(label="TXT Medical Report")
            gr.HTML('</div>')

    gr.HTML('<div class="footer-text">Designed for a cleaner AI healthcare demo • Sanjeevani AI Doctor</div>')

    # Mic stops → transcribe → show in textbox
    mic.stop_recording(
        fn=on_audio_recorded,
        inputs=[mic],
        outputs=[out_transcript],
    )

    # ✅ out_audio is COMPLETELY REMOVED from outputs
    # process() returns 3 values, outputs has 3 components
    submit.click(
        fn=process,
        inputs=[mic, img, lang, txt],
        outputs=[out_transcript, out_response, out_file],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
