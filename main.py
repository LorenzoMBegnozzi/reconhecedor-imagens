from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from utils import salvar_imagem, reconhecer_imagem
from models import Resultado
from db import col  # coleção "imagens"
import io

app = FastAPI(title="Reconhecedor de Imagens")

@app.post("/cadastrar", response_model=Resultado)
async def cadastrar(nome: str = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()
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
            "nome": doc.get("nome") or doc.get("name"), 
            "imagem": doc.get("imageUrl"),
            "ano": doc.get("year")
        })
    return {"status": "ok", "total": len(imagens), "imagens": imagens}

@app.get("/imagem/{nome}")
async def get_imagem(nome: str):
    doc = col.find_one({"nome": nome})
    if not doc or "file_id" not in doc:
        return {"erro": "Imagem não encontrada"}
    file_bytes = fs.get(doc["file_id"]).read()
    return StreamingResponse(io.BytesIO(file_bytes), media_type="image/jpeg")

@app.get("/app", response_class=HTMLResponse)
async def app_page():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reconhecedor de Imagens</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #f0f4ff, #e0f7fa);
                text-align: center; 
            }

            h2 { 
                color: #333; 
                margin-bottom: 20px;
            }

            input { 
                margin: 5px; 
                padding: 10px; 
                width: 80%; 
                max-width: 400px;
                border-radius: 8px;
                border: 1px solid #ccc;
            }

            button { 
                margin: 10px; 
                padding: 12px 18px; 
                font-size: 16px; 
                cursor: pointer; 
                border: none;
                border-radius: 8px;
                background: linear-gradient(90deg, #007bff, #00c6ff);
                color: white;
                transition: all 0.3s ease;
            }

            button:hover { 
                background: linear-gradient(90deg, #0056b3, #0096c7);
                transform: translateY(-2px);
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }

            #mensagem { 
                margin-top: 25px; 
                font-weight: bold; 
                white-space: pre-wrap; 
                text-align: center; 
            }

            #preview { 
                margin-top: 15px; 
            }

            #preview img {
                border-radius: 12px;
                max-width: 200px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            /* Container dos cards em coluna */
            .container {
                display: flex;
                flex-direction: column; /* cards empilhados verticalmente */
                align-items: center;
                gap: 20px;
                margin-top: 25px;
            }

            .card {
                background: linear-gradient(145deg, #ffffff, #e6f0ff);
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
                padding: 15px;
                width: 80%;          /* largura maior */
                max-width: 400px;    /* limita para telas grandes */
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                cursor: pointer;
            }

            .card:hover {
                transform: translateY(-5px) scale(1.03);
                box-shadow: 0 12px 30px rgba(0,0,0,0.25);
            }

            .card img {
                width: 80%;
                border-radius: 12px;
                margin-bottom: 10px;
                object-fit: cover;
                transition: transform 0.3s ease;
            }

            .card img:hover {
                transform: scale(1.05);
            }

            .card b {
                display: block;
                font-size: 16px;
                margin-bottom: 6px;
                color: #333;
            }

            .card p {
                font-size: 14px;
                margin: 2px 0;
                color: #555;
            }
        </style>
    </head>
    <body>
        <h2>📸 Reconhecedor de Imagens</h2>
        <input type="text" id="nome" placeholder="Nome da imagem (para cadastro)"><br>
        <input type="file" id="fileInput" accept="image/*" capture="environment" onchange="previewImagem(event)"><br><br>

        <button onclick="cadastrar()">Cadastrar</button>
        <button onclick="reconhecer()">Reconhecer</button>

        <div id="preview"></div>
        <div id="mensagem"></div>

        <script>
            function previewImagem(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById("preview").innerHTML = `
                            <h3>Imagem enviada:</h3>
                            <img src="${e.target.result}" alt="Preview">
                        `;
                    };
                    reader.readAsDataURL(file);
                }
            }

            async function cadastrar() {
                const nome = document.getElementById("nome").value;
                const fileInput = document.getElementById("fileInput").files[0];
                if (!nome || !fileInput) {
                    document.getElementById("mensagem").innerText = "⚠️ Preencha o nome e selecione uma imagem.";
                    return;
                }
                const formData = new FormData();
                formData.append("nome", nome);
                formData.append("file", fileInput);

                const resp = await fetch("/cadastrar", { method: "POST", body: formData });
                const data = await resp.json();
                document.getElementById("mensagem").innerText = JSON.stringify(data, null, 2);
            }

            async function reconhecer() {
                const fileInput = document.getElementById("fileInput").files[0];
                if (!fileInput) {
                    document.getElementById("mensagem").innerText = "⚠️ Selecione uma imagem para reconhecer.";
                    return;
                }
                const formData = new FormData();
                formData.append("file", fileInput);

                const resp = await fetch("/reconhecer", { method: "POST", body: formData });
                const data = await resp.json();

                if (data.top3 && data.top3.length > 0) {
                    let lista = "<h3>🔎 Top 3 imagens mais parecidas:</h3>";
                    lista += "<div class='container'>";
                    data.top3.forEach((item) => {
                        lista += `
                            <div class='card'>
                                <img src="${item.url}" alt="${item.nome}">
                                <b>${item.nome}</b>
                                <p>🔹 Similaridade: ${(item.similaridade * 100).toFixed(1)}%</p>
                                <p>🔹 Diferença: ${(item.diferenca * 100).toFixed(1)}%</p>
                            </div>
                        `;
                    });
                    lista += "</div>";
                    document.getElementById("mensagem").innerHTML = lista;
                } else {
                    document.getElementById("mensagem").innerText = JSON.stringify(data, null, 2);
                }
            }
        </script>
    </body>
    </html>
    """
