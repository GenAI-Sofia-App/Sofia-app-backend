# 🧠 Asistente Financiero para Migrantes

Este proyecto contiene tres asistentes financieros diferentes, cada uno implementado como una app independiente de Streamlit con capacidades de voz, traducción automática y comprensión contextual multilingüe.

## ✅ Funcionalidades

### 1. 🤝 Soy nuevo aquí
Guía paso a paso para abrir una cuenta bancaria, entender documentación básica, y cómo declarar impuestos en España.

- Usa: `modulo_3_gestion_del_dinero_y_bancos.json`, `modulo_8_declaracion_impuestos.json`, `bancos_productos_funcionalidades_fixed.json`, `modulo_7_recursos_adicionales.json`

### 2. 🏦 Este es tu banco
Sistema de recomendación de entidades bancarias según tu perfil (edad, tipo de uso, situación migratoria).

- Usa: `bancos_productos_funcionalidades_fixed.json`, `modulo_1_fundamentos_de_la_educacion_financiera.json`

### 3. 💡 Aprende a ahorrar
Consejos y microeducación en finanzas personales: ahorro, inversión, planificación, deuda.

- Usa: `modulo_1_fundamentos_de_la_educacion_financiera.json`, `modulo_2_presupuesto_personal_y_familiar.json`, `modulo_5_ahorro_e_inversion_basica.json`, `modulo_6_objetivos_financieros_y_planificacion.json`, `modulo_4_deuda_e_intereses.json`

---

## 🚀 Cómo ejecutar

Requiere Python 3.9 o superior.

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Crea tu archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=sk-xxxxx
```

3. Ejecuta cada app desde su carpeta:

```bash
# Desde soy_nuevo_aqui_backend/
streamlit run soy_nuevo_aqui.py --server.port 8501

# Desde este_es_tu_banco_backend/
streamlit run este_es_tu_banco.py --server.port 8502

# Desde aprende_a_ahorrar_backend/
streamlit run aprende_a_ahorrar.py --server.port 8503
```

---

## 📁 Estructura

```
Sofia-app-backend/
├── docs/                             ← Archivos .json base de conocimiento
├── soy_nuevo_aqui_backend/
│   └── soy_nuevo_aqui.py             ← App 1
├── este_es_tu_banco_backend/
│   └── este_es_tu_banco.py           ← App 2
├── aprende_a_ahorrar_backend/
│   └── aprende_a_ahorrar.py          ← App 3
├── template/
│   └── app.py                        ← Base original
├── requirements.txt
└── README.md
```

---

## 🧠 Notas

- Las rutas a los archivos JSON están resueltas con `../docs/*.json` desde cada subcarpeta.
- Puedes abrir cada herramienta en un `iframe` desde tu frontend Lovable o acceder vía `localhost:{puerto}`.
- Si usas puerto diferente, asegúrate que esté libre.