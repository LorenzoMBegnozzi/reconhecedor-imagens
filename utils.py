from db import db, col
import gridfs
from PIL import Image
import io
import numpy as np
import cv2
import requests
from db import col

fs = gridfs.GridFS(db)

def salvar_imagem(nome: str, file_bytes: bytes):
    file_id = fs.put(file_bytes, filename=nome)
    col.insert_one({"nome": nome, "file_id": file_id})
    print(f"✅ Imagem {nome} salva no MongoDB")


def reconhecer_imagem(file_bytes: bytes):
    try:
        print("📥 Iniciando reconhecimento...")
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        img_np = np.array(img)
        print("✅ Imagem recebida processada")

        img_np = cv2.resize(img_np, (256, 256))
        img_hist = cv2.calcHist([img_np], [0, 1, 2], None, [8, 8, 8],
                                [0, 256, 0, 256, 0, 256])
        img_hist = cv2.normalize(img_hist, img_hist).flatten()

        resultados = []
        total_docs = col.count_documents({})
        print(f"📂 Verificando {total_docs} documentos no MongoDB")

        for doc in col.find():
            stored_img = None
            nome = doc.get("name") or doc.get("nome")

            if "imageUrl" in doc:
                print(f"🔗 Buscando imagem via URL: {nome}")
                try:
                    resp = requests.get(doc["imageUrl"], timeout=5)
                    if resp.status_code == 200:
                        stored_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                except Exception as e:
                    print(f"⚠️ Erro ao baixar {nome}: {e}")
                    continue

            if stored_img is None:
                continue

            stored_np = np.array(stored_img)
            stored_np = cv2.resize(stored_np, (256, 256))
            stored_hist = cv2.calcHist([stored_np], [0, 1, 2], None, [8, 8, 8],
                                       [0, 256, 0, 256, 0, 256])
            stored_hist = cv2.normalize(stored_hist, stored_hist).flatten()

            score = cv2.compareHist(img_hist, stored_hist, cv2.HISTCMP_CORREL)
            print(f"🔸 {nome}: similaridade {score:.3f}")
            resultados.append({
                "nome": nome,
                "url": doc.get("imageUrl"),
                "similaridade": round(float(score), 3),
                "diferenca": round(1 - float(score), 3)
            })

        resultados = sorted(resultados, key=lambda x: x["similaridade"], reverse=True)
        top3 = [r for r in resultados if r["similaridade"] > 0.4][:3]
        print(f"🏁 Finalizado. Top3: {len(top3)} resultados encontrados")

        return {
            "status": "ok" if top3 else "erro",
            "mensagem": "As 3 imagens mais parecidas foram encontradas"
            if top3 else "Nenhuma imagem parecida encontrada",
            "top3": top3
        }

    except Exception as e:
        print(f"💥 Erro: {e}")
        return {"status": "erro", "mensagem": str(e), "top3": []}

