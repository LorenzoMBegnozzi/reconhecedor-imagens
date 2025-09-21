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
        # Converte imagem recebida em vetor
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        img_np = np.array(img)
        img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        img_hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
        img_hist = cv2.normalize(img_hist, img_hist).flatten()

        resultados = []

        # Percorre imagens no banco
        for doc in col.find():
            if "file_id" not in doc:
                continue

            file_id = doc["file_id"]
            stored_bytes = fs.get(file_id).read()

            stored_img = Image.open(io.BytesIO(stored_bytes)).convert("RGB")
            stored_np = np.array(stored_img)
            stored_gray = cv2.cvtColor(stored_np, cv2.COLOR_RGB2GRAY)
            stored_hist = cv2.calcHist([stored_gray], [0], None, [256], [0, 256])
            stored_hist = cv2.normalize(stored_hist, stored_hist).flatten()

            score = cv2.compareHist(img_hist, stored_hist, cv2.HISTCMP_CORREL)

            resultados.append({
                "nome": doc["nome"],
                "similaridade": round(float(score), 3),
                "diferenca": round(1 - float(score), 3)
            })

        # Ordena pela maior similaridade
        resultados = sorted(resultados, key=lambda x: x["similaridade"], reverse=True)

        # Pega só os 3 primeiros
        top3 = resultados[:3]

        return {
            "status": "ok" if top3 else "erro",
            "mensagem": "As 3 imagens mais parecidas foram encontradas" if top3 else "Nenhuma imagem encontrada no banco",
            "top3": top3
        }

    except Exception as e:
        return {"status": "erro", "mensagem": str(e), "top3": []}

