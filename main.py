from fastapi import FastAPI, UploadFile, File, Form
from utils import salvar_imagem, reconhecer_imagem
from models import Resultado
from db import col  # coleção "imagens"

app = FastAPI(title="Reconhecedor de Imagens")


@app.post("/cadastrar", response_model=Resultado)
async def cadastrar(nome: str = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()  # pega os bytes direto do UploadFile
    salvar_imagem(nome, file_bytes)
    return {"status": "ok", "mensagem": f"Imagem {nome} cadastrada com sucesso!"}


@app.post("/reconhecer", response_model=Resultado)
async def reconhecer(file: UploadFile = File(...)):
    file_bytes = await file.read()
    resultado = reconhecer_imagem(file_bytes)
    return resultado


@app.get("/listar")
async def listar():
    imagens = []
    for doc in col.find():
        imagens.append({
            "id": str(doc["_id"]),
            "nome": doc.get("nome")
        })
    return {"status": "ok", "total": len(imagens), "imagens": imagens}
