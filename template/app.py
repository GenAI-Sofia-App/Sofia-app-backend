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

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Inicializar cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configurar página Streamlit
st.set_page_config(page_title="Asistente Migrante", layout="centered")

# Inicializar motor TTS
tts_engine = pyttsx3.init()
available_voices = tts_engine.getProperty('voices')

#  SELECCIÓN MANUAL DE VOZ (COMENTADO)
# voice_options = [f"{v.name} ({v.id})" for v in available_voices]
# if "selected_voice" not in st.session_state:
#     st.session_state.selected_voice = None
# st.sidebar.title("🗣️ Voz del asistente")
# selected_voice_label = st.sidebar.selectbox("Elige una voz disponible:", voice_options)
# for voice in available_voices:
#     label = f"{voice.name} ({voice.id})"
#     if label == selected_voice_label:
#         tts_engine.setProperty('voice', voice.id)
#         st.session_state.selected_voice = voice.id
#         break

# Selección automática de voz en español
for voice in available_voices:
    if "spanish" in voice.name.lower() or "es" in voice.id.lower() or "pablo" in voice.name.lower():
        tts_engine.setProperty('voice', voice.id)
        break

tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 1.0)

# Bloqueo para evitar múltiples ejecuciones simultáneas de runAndWait
speak_lock = threading.Lock()

# Función segura para hablar con pyttsx3
def speak(text):
    def run():
        if not speak_lock.locked():
            with speak_lock:
                try:
                    tts_engine.say(text)
                    tts_engine.runAndWait()
                except RuntimeError as e:
                    print("Error al hablar:", e)
    threading.Thread(target=run).start()

# Función para transcribir voz (sin detección de idioma)
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

# Cargar base de conocimiento
@st.cache_data
def load_base_knowledge():
    with open("base_doc.json", "r", encoding="utf-8") as f:
        return json.load(f)

base_knowledge = load_base_knowledge()

# Inicializar sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
if "listening" not in st.session_state:
    st.session_state.listening = False

# Interfaz de chat
st.title("🤖 Asistente Financiero para Migrantes")
st.markdown("Pregunta por texto o voz. Puedes cargar tus documentos también.")

# Mostrar mensajes anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Generar respuesta del asistente
def chat_with_gpt(user_msg):
    prompt_sistema = f"""
Eres un asistente financiero para migrantes en España. Debes responder de forma clara, precisa y empática. Usa esta base:
- Apertura cuenta: {base_knowledge['cuenta_bancaria']}
- IRPF: {base_knowledge['irpf']}
- Remesas: {base_knowledge['remesas']}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt_sistema},
            *st.session_state.messages,
            {"role": "user", "content": user_msg}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# Entrada de texto y botón de voz (en columnas)
col1, col2 = st.columns([4, 1])

with col1:
    prompt = st.chat_input("Escribe aquí tu pregunta")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        full_response = chat_with_gpt(prompt)
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Botón de voz con estado dinámico
with col2:
    if st.session_state.listening:
        st.button("🎧 Escuchando...", disabled=True)
    else:
        if st.button("🎙️ Voz"):
            st.session_state.listening = True
            st.rerun()

# Ejecutar transcripción si se activó el estado de escucha
if st.session_state.listening:
    user_voice = whisper_transcribe()
    st.info(f"Tú dijiste: {user_voice}")
    st.session_state.messages.append({"role": "user", "content": user_voice})
    with st.chat_message("user"):
        st.markdown(user_voice)
    with st.chat_message("assistant"):
        full_response = chat_with_gpt(user_voice)
        st.markdown(full_response)
        speak(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.listening = False
    st.rerun()

# Carga de documentos (simulada)
st.divider()
st.subheader("📄 Subir un documento (simulado)")
uploaded = st.file_uploader("Sube tu pasaporte/NIE (PDF o imagen)", type=["pdf", "jpg", "png"])
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded.name[-4:]) as tmp:
        tmp.write(uploaded.read())
        st.success(f"✅ Documento '{uploaded.name}' subido correctamente (simulado)")
        st.markdown("ℹ️ En una versión futura, procesaremos automáticamente este archivo.")
