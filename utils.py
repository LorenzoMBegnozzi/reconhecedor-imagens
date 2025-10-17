from db import db, col
import gridfs
from PIL import Image
import io
import numpy as np
import cv2

# sistema de arquivos dentro do Mongo
fs = gridfs.GridFS(db)


def salvar_imagem(nome: str, file_bytes: bytes):
    """Salva a imagem no MongoDB (GridFS + coleção de metadados)."""
    file_id = fs.put(file_bytes, filename=nome)
    col.insert_one({"nome": nome, "file_id": file_id})
    print(f"✅ Imagem {nome} salva no MongoDB")


def reconhecer_imagem(file_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        img_np = np.array(img)
        img_np = cv2.resize(img_np, (256, 256))
        img_hist = cv2.calcHist([img_np], [0, 1, 2], None, [8, 8, 8],
                                [0, 256, 0, 256, 0, 256])
        img_hist = cv2.normalize(img_hist, img_hist).flatten()

        resultados = []

        for doc in col.find():
            if "file_id" not in doc:
                continue

            file_id = doc["file_id"]
            stored_bytes = fs.get(file_id).read()

            stored_img = Image.open(io.BytesIO(stored_bytes)).convert("RGB")
            stored_np = np.array(stored_img)
            stored_np = cv2.resize(stored_np, (256, 256))
            stored_hist = cv2.calcHist([stored_np], [0, 1, 2], None, [8, 8, 8],
                                       [0, 256, 0, 256, 0, 256])
            stored_hist = cv2.normalize(stored_hist, stored_hist).flatten()

            score = cv2.compareHist(img_hist, stored_hist, cv2.HISTCMP_CORREL)
            resultados.append({
                "nome": doc["nome"],
                "similaridade": round(float(score), 3),
                "diferenca": round(1 - float(score), 3)
            })

        # Ordena e pega top 3
        resultados = sorted(resultados, key=lambda x: x["similaridade"], reverse=True)
        resultados = [r for r in resultados if r["similaridade"] > 0.3]
        top3 = resultados[:3]

        return {
            "status": "ok" if top3 else "erro",
            "mensagem": "As 3 imagens mais parecidas foram encontradas" if top3 else "Nenhuma imagem parecida encontrada",
            "top3": top3
        }

    except Exception as e:
        return {"status": "erro", "mensagem": str(e), "top3": []}

