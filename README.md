
# 🧠 Asistente Financiero para Migrantes (Demo)

Esta es una demo en Streamlit que actúa como asistente financiero inclusivo para personas migrantes. Incluye:

- 💬 Chat multilingüe con GPT-4o (texto y voz)
- 🎙 Entrada por voz usando Whisper API
- 🔊 Salida por voz con pyttsx3 (o gTTS opcional)
- 📄 Subida de documentos (simulada)
- 📚 Base documental local (`base_doc.json`)

## 🚀 Cómo ejecutar

1. Clona el repositorio o descomprime el ZIP.

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Crea un archivo `.env`:

```env
OPENAI_API_KEY=sk-xxxxx
```

4. Ejecuta la app:

Mediante:
```bash
streamlit run app.py
```

o mediante:

```bash
python -m streamlit run app.py
```

## 📁 Estructura

```
asistente_migrante_demo/
├── app.py               # Aplicación principal en Streamlit
├── base_doc.json        # Base de conocimiento usada en el prompt
├── requirements.txt     # Dependencias de Python
├── .env.example         # Plantilla del archivo de variables
└── README.md            # Este archivo
```

## ⚠️ Notas

- Si tienes errores con `pyttsx3`, instala `espeak` en tu sistema o reemplázalo con `gTTS`.
- Whisper requiere acceso a la API de OpenAI para STT (voz a texto).

