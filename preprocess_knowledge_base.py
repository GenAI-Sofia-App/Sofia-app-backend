import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # Because script is in root
persist_dir = os.path.join(PROJECT_ROOT, "chroma_db")
print("ChromaDB directory:", persist_dir)

import json
from openai import OpenAI
import chromadb

# Setup OpenAI client
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def openai_embed(texts):
    # Takes a list of strings, returns a list of embedding lists
    response = client_openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]

def flatten_bank(bank_name, bank_data):
    """Extract features and products as separate docs from a bank entry (bank_data)."""
    def get(d, k):
        return d.get(k, "")

    documents = []
    metadatas = []

    # Process funcionalidades
    funcionalidades = bank_data.get("funcionalidades", {})
    for func_name, func in funcionalidades.items():
        if not isinstance(func, dict):
            continue
        text = (
            f"{bank_name} - Funcionalidad: {func_name}\n"
            f"Descripción: {get(func, 'descripcion')}\n"
            f"Requisitos: {get(func, 'requisitos')}\n"
            f"Modalidad: {get(func, 'modalidad') or get(func, 'proceso')}\n"
            f"Beneficios: {get(func, 'beneficios')}\n"
        )
        documents.append(text)
        metadatas.append({
            "bank": bank_name,
            "type": "funcionalidad",
            "name": func_name
        })

    # Process productos
    productos = bank_data.get("productos", {})
    for prod_name, prod in productos.items():
        if not isinstance(prod, dict):
            continue
        text = (
            f"{bank_name} - Producto: {prod_name}\n"
            f"Descripción: {get(prod, 'descripcion')}\n"
            f"Requisitos: {get(prod, 'requisitos')}\n"
            f"Modalidad: {get(prod, 'modalidad') or get(prod, 'proceso')}\n"
            f"Beneficios: {get(prod, 'beneficios')}\n"
        )
        documents.append(text)
        metadatas.append({
            "bank": bank_name,
            "type": "producto",
            "name": prod_name
        })
    return documents, metadatas

chroma_client = chromadb.PersistentClient(path=persist_dir)

### --- INDEX BANKS --- ###
with open("docs/bancos_productos_funcionalidades.json", encoding="utf-8") as f:
    banks = json.load(f)

all_texts = []
all_metadatas = []

# Correct way: iterate over items!
for bank_name, bank_data in banks.items():
    if not isinstance(bank_data, dict):
        continue
    docs, metas = flatten_bank(bank_name, bank_data)
    all_texts.extend(docs)
    all_metadatas.extend(metas)

embeddings = openai_embed(all_texts)

if "banks" in [col.name for col in chroma_client.list_collections()]:
    chroma_client.delete_collection("banks")
col_banks = chroma_client.create_collection("banks")

for idx, (text, emb, meta) in enumerate(zip(all_texts, embeddings, all_metadatas)):
    col_banks.add(
        ids=[str(idx)],
        embeddings=[emb],
        documents=[text],
        metadatas=[meta]
    )

print(f"✔ Banks indexed: {len(all_texts)} documents.")


### --- INDEX FINANCIAL FUNDAMENTALS --- ###
with open("docs/modulo_1_fundamentos_de_la_educacion_financiera.json", encoding="utf-8") as f:
    fundamentos = json.load(f)

fundamentals_texts = []
fundamentals_metadatas = []

for item in fundamentos:
    # Convertir preguntas y respuestas frecuentes a texto
    preguntas_frecuentes = item.get("preguntas_frecuentes", [])
    preguntas_texto = []
    for faq in preguntas_frecuentes:
        pregunta = faq.get("pregunta", "")
        respuesta = faq.get("respuesta", "")
        preguntas_texto.append(f"P: {pregunta}\nR: {respuesta}")
    preguntas_str = "\n".join(preguntas_texto)

    text = (
        f"Concepto: {item.get('concepto', '')}\n"
        f"Definición: {item.get('definicion', '')}\n"
        f"Ejemplo: {item.get('ejemplo', '')}\n"
        f"Preguntas frecuentes:\n{preguntas_str}"
    )
    fundamentals_texts.append(text)
    fundamentals_metadatas.append({
        "concepto": item.get("concepto", ""),
        "ejemplo": item.get("ejemplo", ""),
        "preguntas_frecuentes": preguntas_str
    })

fundamentals_embeddings = openai_embed(fundamentals_texts)

if "fundamentals" in [col.name for col in chroma_client.list_collections()]:
    chroma_client.delete_collection("fundamentals")
col_fundamentals = chroma_client.create_collection("fundamentals")

for idx, (text, emb, meta) in enumerate(zip(fundamentals_texts, fundamentals_embeddings, fundamentals_metadatas)):
    col_fundamentals.add(
        ids=[str(idx)],
        embeddings=[emb],
        documents=[text],
        metadatas=[meta]
    )

print(f"✔ Fundamentals indexed: {len(fundamentals_texts)} documents.")

file_to_collection = {
    "modulo_2_presupuesto_personal_y_familiar.json": "budget",
    "modulo_4_deuda_e_intereses.json": "debt",
    "modulo_5_ahorro_e_inversion_basica.json": "saving",
    "modulo_6_objetivos_financieros_y_planificacion.json": "planning",
    "modulo_3_gestion_del_dinero_y_bancos.json": "banking",
    "modulo_7_recursos_adicionales.json": "resources",
    "modulo_8_declaracion_impuestos.json": "taxes"
}

for filename, collection_name in file_to_collection.items():
    file_path = os.path.join("docs", filename)
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    metas = []

    temas = data.get("temas", [])
    for tema in temas:
        tema_id = tema.get("id", "")
        tema_titulo = tema.get("titulo", "")
        for item in tema.get("contenido", []):
            pregunta = item.get("pregunta", "")
            respuesta = item.get("respuesta", "")
            doc_text = (
                f"Tema: {tema_titulo}\n"
                f"Pregunta: {pregunta}\n"
                f"Respuesta: {respuesta}"
            )
            docs.append(doc_text)
            metas.append({
                "tema_id": tema_id,
                "tema_titulo": tema_titulo,
                "pregunta": pregunta
            })

    if not docs:
        continue

    embeddings = openai_embed(docs)

    # Recreate collection to avoid duplicates
    if collection_name in [col.name for col in chroma_client.list_collections()]:
        chroma_client.delete_collection(collection_name)
    collection = chroma_client.create_collection(collection_name)

    for idx, (text, emb, meta) in enumerate(zip(docs, embeddings, metas)):
        collection.add(
            ids=[str(idx)],
            embeddings=[emb],
            documents=[text],
            metadatas=[meta]
        )

    print(f"✔ Indexed {filename} as '{collection_name}': {len(docs)} Q&As.")

print("✅ All modules indexed in ChromaDB.")
