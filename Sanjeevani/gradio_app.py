# import os
# import base64
# import gradio as gr
# from input_voice import transcribe_audio_and_detect_language
# from output_voice import text_to_speech_with_murf, murf_translate, VOICE_MAP
# from groq import Groq

# from dotenv import load_dotenv
# import os

# load_dotenv()   # ✅ ye sab env variables load karega

# GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# LANG_CHOICES = [
#     ("English", "en-US"), ("French", "fr-FR"), ("German", "de-DE"), ("Spanish", "es-ES"),
#     ("Italian", "it-IT"), ("Portuguese", "pt-BR"), ("Chinese", "zh-CN"), ("Dutch", "nl-NL"),
#     ("Hindi", "hi-IN"), ("Korean", "ko-KR"), ("Tamil", "ta-IN"), ("Polish", "pl-PL"),
#     ("Bengali", "bn-IN"), ("Japanese", "ja-JP"), ("Greek", "el-GR"), ("Romanian", "ro-RO"),
#     ("Slovak", "sk-SK")
# ]

# lang_code_map = {label: code for label, code in LANG_CHOICES}

# def encode_image_base64(path: str) -> str:
#     with open(path, "rb") as f:
#         return base64.b64encode(f.read()).decode("utf-8")
    
# from typing import Optional, Any, List, Dict, cast
# from groq import Groq

# def analyze_with_groq(prompt: str, image_b64: Optional[str] = None) -> str:
#     client = Groq(api_key=GROQ_API_KEY)

#     content: List[Dict[str, Any]] = [
#         {"type": "text", "text": prompt}
#     ]

#     if image_b64:
#         content.append({
#             "type": "image_url",
#             "image_url": {
#                 "url": f"data:image/jpeg;base64,{image_b64}"
#             }
#         })

#     resp = client.chat.completions.create(
#         model=LLM_MODEL,
#         messages=cast(Any, [
#             {
#                 "role": "user",
#                 "content": content
#             }
#         ])
#     )

#     return (resp.choices[0].message.content or "").strip()

# def save_response_to_txt(text):
#     out_path = "doctor_advice.txt"
#     with open(out_path, "w", encoding="utf-8") as f:
#         f.write(text.strip())
#     return out_path

# def process(audio_path, image_path, lang_code, txt_file):
#     transcript = ""
#     input_lang = "en"

#     if txt_file:
#         with open(txt_file.name, "r", encoding="utf-8") as f:
#             transcript = f.read()
#     elif audio_path:
#         transcript, input_lang = transcribe_audio_and_detect_language(audio_path)

#     if not transcript and image_path:
#         prompt = (
#             "You are an experienced medical doctor. Analyze the uploaded medical image and provide a clear, structured response in simple language. "
#             "Do not say you are an AI. Do not add any disclaimer or preamble. "
#             "Explain the result in the following format:\n\n"
#             "1. Possible Disease/Condition: Mention the most likely disease or condition.\n"
#             "2. Why It May Have Happened: Explain the possible causes or reasons.\n"
#             "3. How It Can Be Treated: Explain what the person should generally do to recover.\n"
#             "4. Medicines Usually Given: Mention the type of medicines commonly used for this kind of condition. Do not mention exact prescription dosage unless clearly safe.\n"
#             "5. Home Remedies: Mention useful home care or lifestyle remedies.\n"
#             "6. What Can Happen If Ignored: Explain possible risks or complications if the condition is not treated.\n\n"
#             "Keep the answer practical, human-like, and easy to understand."
#         )
#     else:
#         prompt = (
#             "You are an experienced medical doctor. Based on the symptoms described below, provide a clear, structured medical response in simple language. "
#             "Do not say you are an AI. Do not include any preamble. "
#             "Explain in the following format:\n\n"
#             "1. Possible Disease/Condition: Mention the most likely disease or condition.\n"
#             "2. Why It May Have Happened: Explain the possible causes or reasons.\n"
#             "3. How It Can Be Treated: Explain what the person should generally do to recover.\n"
#             "4. Medicines Usually Given: Mention the type of medicines commonly used for this kind of condition. Do not mention exact prescription dosage unless clearly safe.\n"
#             "5. Home Remedies: Mention useful home remedies or supportive care.\n"
#             "6. What Can Happen If Ignored: Explain possible future complications.\n\n"
#             "Symptoms:\n"
#             f"{transcript}\n\n"
#             "Keep the answer practical, well-structured, and easy for a normal person to understand."
#         )

#     image_b64 = encode_image_base64(image_path) if image_path else None
#     doctor_response = analyze_with_groq(prompt, image_b64)

#     # Translate if necessary
#     target_lang = lang_code.split("-")[0]
#     if target_lang != input_lang:
#         doctor_response = murf_translate(doctor_response, lang_code)

#     _, voice_id = VOICE_MAP.get(lang_code, VOICE_MAP["en-US"])
#     out_wav = f"doctor_response_{lang_code}.wav"
#     text_to_speech_with_murf(doctor_response, out_wav, voice_id)

#     txt_path = save_response_to_txt(doctor_response)
#     return transcript or "🖼️ Image-only analysis", doctor_response, out_wav, txt_path

# # UI Setup
# LOGO_PATH = "logo.png"
# with open(LOGO_PATH, "rb") as f:
#     logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# css = """body { background: linear-gradient(145deg, #0f172a, #1e293b); color: white; font-family: 'Segoe UI'; }"""

# with gr.Blocks(css=css) as demo:
#     gr.HTML(f'''
#     <div style="display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 10px;">
#         <img src="data:image/png;base64,{logo_b64}" width="100">
#     </div>
# ''')

#     gr.HTML("<h1 style='text-align:center;color:#fcd34d;'>🌍 Sanjeevani - Multilingual AI Doctor</h1>")

#     with gr.Row():
#         with gr.Column(elem_classes="gr-box"):
#             mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Speak your concern")
#             img = gr.Image(type="filepath", label="📷 Upload image (optional)")
#             txt = gr.File(label="📄 Or Upload Symptom .txt", file_types=[".txt"])
#             lang = gr.Dropdown(choices=[label for label, _ in LANG_CHOICES], value="English", label="🌐 Response Language")
#             submit = gr.Button("🩺 Diagnose")

#         with gr.Column(elem_classes="gr-box"):
#             out1 = gr.Textbox(label="📝 Transcription")
#             out2 = gr.Textbox(label="💬 Doctor's Response")
#             out3 = gr.Audio(type="filepath", label="🔊 Voice Response")
#             out4 = gr.File(label="📄 Download TXT Report")

#     def wrapped_process(mic, img, lang_label, txt):
#         return process(mic, img, lang_code_map[lang_label], txt)

#     submit.click(wrapped_process, inputs=[mic, img, lang, txt], outputs=[out1, out2, out3, out4])

# if __name__ == "__main__":
#     demo.launch(server_name="0.0.0.0", server_port=10000)
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
# http://localhost:5174/voices
AVATAR_FRONTEND_URL = "http://localhost:5173"
LIP_SYNC_URL = "http://localhost:3000/lip-sync"

# -------------------- CONFIG --------------------
LANGUAGE_MAP = {
    "English": "en-US",
    "Hindi": "hi-IN"
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

# -------------------- HELPERS --------------------
def get_target_lang(lang_label: str) -> str:
    return LANGUAGE_MAP.get(lang_label, "hi-IN")


def read_text_file(txt_file) -> str:
    if not txt_file:
        return ""

    try:
        with open(txt_file.name, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print("TXT read error:", e)
        return ""


def get_transcript(audio_path: str, txt_file):
    transcript = ""
    detected_lang = "en"

    txt_content = read_text_file(txt_file)
    if txt_content:
        return txt_content, detected_lang

    if audio_path:
        try:
            transcript, detected_lang = transcribe_audio_and_detect_language(audio_path)
            transcript = transcript.strip() if transcript else ""
        except Exception as e:
            print("Audio transcription error:", e)
            traceback.print_exc()

    return transcript, detected_lang


# def build_prompt(transcript: str, image_path=None) -> str:
#     if transcript:
#         return f"""
# You are an experienced medical doctor. Provide a clear, structured response in simple language.

# Format strictly like this:

# 1. Possible Disease/Condition: ...
# 2. Why It May Have Happened: ...
# 3. How It Can Be Treated: ...
# 4. Medicines Usually Given: ... (no exact dosage)
# 5. Home Remedies: ...
# 6. What Can Happen If Ignored: ...

# Symptoms:
# {transcript}

# Rules:
# - Keep it practical and easy to understand.
# - Do not give exact dosage.
# - Do not claim certainty.
# - Suggest consulting a real doctor for serious symptoms.
# """.strip()

#     elif image_path:
#         return """
# You are an experienced medical doctor.

# The user uploaded a medical image but did not provide symptoms text.
# Respond carefully in simple language using this exact format:

# 1. Possible Disease/Condition: ...
# 2. Why It May Have Happened: ...
# 3. How It Can Be Treated: ...
# 4. Medicines Usually Given: ... (no exact dosage)
# 5. Home Remedies: ...
# 6. What Can Happen If Ignored: ...

# Rules:
# - Since no text symptoms are given, clearly say this is only a possible observation.
# - Do not claim certainty.
# - Recommend consulting a qualified doctor for diagnosis.
# """.strip()

#     else:
#         return """
# You are an experienced medical doctor.

# The user did not provide enough symptom details.
# Respond in simple language and ask for more symptoms using this format:

# 1. Possible Disease/Condition: Not enough information
# 2. Why It May Have Happened: More symptom details are needed
# 3. How It Can Be Treated: Please describe symptoms clearly
# 4. Medicines Usually Given: Consult a doctor before taking medicine
# 5. Home Remedies: Rest, hydration, and monitoring symptoms
# 6. What Can Happen If Ignored: Serious illness may be missed

# Keep the response practical and easy to understand.
# """.strip()

def build_prompt(transcript: str, image_path=None) -> str:
    if transcript:
        return f"""
You are a doctor. Give a short, simple response in this format:
1. Possible Condition:
2. Cause:
3. Treatment:
4. Common Medicines: (no dosage)
5. Home Care:
6. Risk if Ignored:

Symptoms: {transcript}

Rules:
- Simple language
- No certainty
- Advise doctor if serious
""".strip()

    elif image_path:
        return """
You are a doctor. The user uploaded a medical image without symptom text.
Reply in this format:
1. Possible Condition:
2. Cause:
3. Treatment:
4. Common Medicines: (no dosage)
5. Home Care:
6. Risk if Ignored:

Rules:
- This is only a possible observation
- No certainty
- Advise doctor consultation
""".strip()

    else:
        return """
You are a doctor. Not enough symptom details were given.
Reply in this format:
1. Possible Condition: Not enough information
2. Cause: More details needed
3. Treatment: Describe symptoms clearly
4. Common Medicines: Consult a doctor
5. Home Care: Rest, fluids, monitor symptoms
6. Risk if Ignored: Serious illness may be missed
""".strip()


def call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Error: GROQ_API_KEY not found. Please add it in your .env file."

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        content = response.choices[0].message.content
        return content.strip() if content else "No response generated by the model."

    except Exception as e:
        print("Groq API error:", e)
        traceback.print_exc()
        return f"Error while generating doctor advice: {str(e)}"


def translate_response(text: str, target_lang: str) -> str:
    try:
        if target_lang.startswith("en"):
            return text

        translated = murf_translate(text, target_lang)
        return translated.strip() if translated else text

    except Exception as e:
        print("Translation error:", e)
        traceback.print_exc()
        return text


def generate_tts(text: str, target_lang: str):
    try:
        _, voice_id = VOICE_MAP.get(target_lang, VOICE_MAP["en-US"])
        out_wav = f"doctor_response_{target_lang}.wav"
        text_to_speech_with_murf(text, out_wav, voice_id)

        if os.path.exists(out_wav):
            return out_wav

        return None

    except Exception as e:
        print("TTS error:", e)
        traceback.print_exc()
        return None


def send_to_avatar(text: str, wav_path):
    if not wav_path or not os.path.exists(wav_path):
        print("Avatar send skipped: audio file not found")
        return

    try:
        with open(wav_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = requests.post(
            LIP_SYNC_URL,
            json={"text": text, "audioBase64": audio_base64},
            timeout=15
        )

        print("Avatar response status:", response.status_code)

    except Exception as e:
        print("Avatar send error:", e)
        traceback.print_exc()


def save_report(text: str) -> str:
    txt_path = "doctor_advice.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print("TXT save error:", e)
        traceback.print_exc()
    return txt_path


# -------------------- MAIN PROCESS --------------------
def process(audio_path, image_path, lang_label, txt_file):
    try:
        target_lang = get_target_lang(lang_label)

        transcript, input_lang = get_transcript(audio_path, txt_file)
        prompt = build_prompt(transcript, image_path)
        doctor_response = call_groq(prompt)

        doctor_response = translate_response(doctor_response, target_lang)
        out_wav = generate_tts(doctor_response, target_lang)
        send_to_avatar(doctor_response, out_wav)
        txt_path = save_report(doctor_response)

        final_transcript = transcript if transcript else "No speech/text symptoms provided."

        return (
            final_transcript,
            doctor_response,
            out_wav,
            txt_path
        )

    except Exception as e:
        print("Unexpected process error:", e)
        traceback.print_exc()

        error_msg = f"Unexpected error: {str(e)}"
        txt_path = save_report(error_msg)

        return (
            "Error while processing input.",
            error_msg,
            None,
            txt_path
        )


# ====================== GRADIO UI ======================
with gr.Blocks(title="Sanjeevani AI Doctor", css=CUSTOM_CSS) as demo:
    gr.HTML("""
        <div class="main-title">🌍 Sanjeevani - AI Doctor with 3D Avatar</div>
        <div class="sub-title">
            Smart AI medical guidance with voice input, multilingual response, and a talking 3D doctor avatar
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🩺 Patient Input</div>')
            gr.HTML('<div class="section-note">Speak your concern, upload a report text file, or add an optional medical image.</div>')

            mic = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎙️ Speak your concern"
            )

            img = gr.Image(
                type="filepath",
                label="📷 Upload medical image (optional)"
            )

            txt = gr.File(
                label="📄 Or upload symptoms .txt",
                file_types=[".txt"]
            )

            lang = gr.Dropdown(
                choices=["English", "Hindi"],
                value="Hindi",
                label="🌐 Response Language"
            )

            submit = gr.Button("🧑‍⚕️ Get Diagnosis", elem_classes="primary-btn")
            gr.HTML('</div>')

        with gr.Column(scale=1):
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🧑‍⚕️ 3D Talking Doctor Avatar</div>')
            gr.HTML('<div class="section-note">Your AI doctor will speak the generated response through the connected avatar system.</div>')

            gr.HTML(f"""
                <div class="avatar-frame">
                    <iframe
                        src="{AVATAR_FRONTEND_URL}"
                        width="100%"
                        height="650"
                        style="border:none;">
                    </iframe>
                </div>
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
                placeholder="Your speech or uploaded text will appear here..."
            )
            gr.HTML('</div>')

        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">💬 Doctor Response</div>')
            out_response = gr.Textbox(
                label="Doctor's Advice",
                lines=12,
                placeholder="Generated medical guidance will appear here..."
            )
            gr.HTML('</div>')

    gr.HTML("<br>")

    with gr.Row():
        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">🔊 Voice Response</div>')
            out_audio = gr.Audio(label="Audio Output", type="filepath")
            gr.HTML('</div>')

        with gr.Column():
            gr.HTML('<div class="glass-card">')
            gr.HTML('<div class="section-heading">📄 Download Report</div>')
            out_file = gr.File(label="TXT Medical Report")
            gr.HTML('</div>')

    gr.HTML('<div class="footer-text">Designed for a cleaner AI healthcare demo experience • Sanjeevani AI Doctor</div>')

    submit.click(
        fn=process,
        inputs=[mic, img, lang, txt],
        outputs=[out_transcript, out_response, out_audio, out_file]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)