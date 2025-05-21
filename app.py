import streamlit as st
import openai
import os
import speech_recognition as sr
import pyttsx3
import tempfile
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Asistente Migrante", layout="centered")
tts_engine = pyttsx3.init()

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def whisper_transcribe():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Escuchando...")
        audio = r.listen(source)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        with open(tmp.name, "wb") as f:
            f.write(audio.get_wav_data())
        with open(tmp.name, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript['text']

@st.cache_data
def load_base_knowledge():
    with open("base_doc.json", "r", encoding="utf-8") as f:
        return json.load(f)

base_knowledge = load_base_knowledge()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 Asistente Financiero para Migrantes")
st.markdown("Pregunta por texto o voz. Puedes cargar tus documentos también.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def chat_with_gpt(user_msg):
    prompt_sistema = f"""
Eres un asistente financiero para migrantes en España. Debes responder de forma clara, precisa y empática. Usa esta base:
- Apertura cuenta: {base_knowledge['cuenta_bancaria']}
- IRPF: {base_knowledge['irpf']}
- Remesas: {base_knowledge['remesas']}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt_sistema},
            *st.session_state.messages,
            {"role": "user", "content": user_msg}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

if prompt := st.chat_input("Escribe aquí tu pregunta"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        full_response = chat_with_gpt(prompt)
        st.markdown(full_response)
        speak(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.button("🎙️ Hablar con el asistente"):
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

st.divider()
st.subheader("📄 Subir un documento (simulado)")
uploaded = st.file_uploader("Sube tu pasaporte/NIE (PDF o imagen)", type=["pdf", "jpg", "png"])
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded.name[-4:]) as tmp:
        tmp.write(uploaded.read())
        st.success(f"✅ Documento '{uploaded.name}' subido correctamente (simulado)")
        st.markdown("ℹ️ En una versión futura, procesaremos automáticamente este archivo.")
