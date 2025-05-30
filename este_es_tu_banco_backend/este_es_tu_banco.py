import streamlit as st
from openai import OpenAI
import os
import speech_recognition as sr
import pyttsx3
import tempfile
import json
from dotenv import load_dotenv
from pathlib import Path
import threading
from langdetect import detect
from deep_translator import GoogleTranslator

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
st.set_page_config(page_title="Asistente Migrante", layout="centered")

tts_engine = pyttsx3.init()
available_voices = tts_engine.getProperty('voices')
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 1.0)

# Bloqueo para el TTS
speak_lock = threading.Lock()

def speak(text, lang="es"):
    def run():
        with speak_lock:
            try:
                st.session_state.speaking = True  # 🚫 Bloquear entrada mientras habla
                for voice in available_voices:
                    if lang == "en" and "english" in voice.name.lower():
                        tts_engine.setProperty('voice', voice.id)
                        break
                    elif lang == "es" and "spanish" in voice.name.lower():
                        tts_engine.setProperty('voice', voice.id)
                        break
                tts_engine.say(text)
                tts_engine.runAndWait()
            except RuntimeError as e:
                print("Error al hablar:", e)
            finally:
                st.session_state.speaking = False  # ✅ Permitir entrada nuevamente
    threading.Thread(target=run).start()

def whisper_transcribe():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Escuchando...")
        audio = r.listen(source)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        with open(tmp.name, "wb") as f:
            f.write(audio.get_wav_data())
        with open(tmp.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
    return transcript.text

def chat_with_gpt(user_msg):
    detected_lang = detect(user_msg)
    translated_input = user_msg
    if detected_lang != "es":
        try:
            translated_input = GoogleTranslator(source=detected_lang, target="es").translate(user_msg)
        except Exception:
            pass

    prompt_sistema = f"""
Eres un asistente que recomienda entidades bancarias según el perfil del usuario (edad, situación migratoria, uso de Bizum, remesas, ahorro). Sé claro y empático. Usa esta base:
- Bancos y productos: {base_knowledge['bancos']}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": translated_input}
        ],
        temperature=0.3
    )

    full_response = response.choices[0].message.content

    if detected_lang != "es":
        try:
            full_response = GoogleTranslator(source="es", target=detected_lang).translate(full_response)
        except Exception:
            pass

    return full_response, detected_lang

@st.cache_data
def load_base_knowledge():
    base = {}
    with open(Path("docs/bancos_productos_funcionalidades.json"), "r", encoding="utf-8") as f:
        base["bancos"] = json.load(f)
    with open(Path("docs/modulo_1_fundamentos_de_la_educacion_financiera.json"), "r", encoding="utf-8") as f:
        base["fundamentos"] = json.load(f)
    return base

base_knowledge = load_base_knowledge()

# Estado
if "messages" not in st.session_state:
    st.session_state.messages = []
if "listening" not in st.session_state:
    st.session_state.listening = False
if "voice_response_pending" not in st.session_state:
    st.session_state.voice_response_pending = None
if "voice_response_lang" not in st.session_state:
    st.session_state.voice_response_lang = None
if "speaking" not in st.session_state:
    st.session_state.speaking = False

st.title("🏦 Este es tu banco")
st.markdown("Pregunta por texto o voz. Puedes cargar tus documentos también.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada texto / voz
col1, col2 = st.columns([4, 1])

with col1:
    if st.session_state.get("speaking", False):
        st.chat_input("🗣️ Reproduciendo respuesta...", disabled=True)
    else:
        prompt = st.chat_input("Escribe aquí tu pregunta")

if "prompt" in locals() and prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        full_response, lang = chat_with_gpt(prompt)
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

with col2:
    if st.session_state.listening:
        st.button("🎧 Escuchando...", disabled=True)
    else:
        if st.button("🎙️ Voz"):
            st.session_state.listening = True
            st.rerun()

# Reproducir voz tras rerun
if st.session_state.voice_response_pending:
    with st.status("🗣️ Reproduciendo respuesta...", expanded=False):
        speak(st.session_state.voice_response_pending, st.session_state.voice_response_lang)
    st.session_state.voice_response_pending = None
    st.session_state.voice_response_lang = None

# Voz
if st.session_state.listening:
    user_voice = whisper_transcribe()
    detected_lang = detect(user_voice)
    st.info(f"Tú dijiste: {user_voice}")
    st.session_state.messages.append({"role": "user", "content": user_voice})

    with st.chat_message("user"):
        st.markdown(user_voice)
    with st.chat_message("assistant"):
        full_response, lang = chat_with_gpt(user_voice)
        st.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.voice_response_pending = full_response
    st.session_state.voice_response_lang = lang
    st.session_state.listening = False
    st.rerun()

# Documentos
st.divider()
st.subheader("📄 Subir un documento (simulado)")
uploaded = st.file_uploader("Sube tu pasaporte/NIE (PDF o imagen)", type=["pdf", "jpg", "png"])
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded.name[-4:]) as tmp:
        tmp.write(uploaded.read())
        st.success(f"✅ Documento '{uploaded.name}' subido correctamente (simulado)")
        st.markdown("ℹ️ En una versión futura, procesaremos automáticamente este archivo.")
