from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from utils import salvar_imagem, reconhecer_imagem
from models import Resultado
from db import col  # coleção "imagens"
from fastapi.responses import StreamingResponse


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
            "nome": doc.get("nome") or doc.get("name"), 
            "imagem": doc.get("imageUrl"),
            "ano": doc.get("year")
        })
    return {"status": "ok", "total": len(imagens), "imagens": imagens}

@app.get("/imagem/{nome}")
async def get_imagem(nome: str):
    """Retorna a imagem armazenada no MongoDB pelo nome."""
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
                margin: 20px; 
                text-align: center; 
                background: #f7f7f7;
            }
            h2 { color: #333; }
            button { 
                margin: 10px; 
                padding: 12px 18px; 
                font-size: 16px; 
                cursor: pointer; 
                border: none;
                border-radius: 8px;
                background-color: #007bff;
                color: white;
            }
            button:hover { background-color: #0056b3; }
            #mensagem { 
                margin-top: 20px; 
                font-weight: bold; 
                white-space: pre-wrap; 
                text-align: center; 
            }
            input { margin: 5px; padding: 10px; width: 80%; }
            #preview { margin-top: 15px; }
            img { border-radius: 10px; }
            .container { 
                display: flex; 
                justify-content: center; 
                align-items: flex-start; 
                gap: 25px; 
                flex-wrap: wrap;
                margin-top: 20px;
            }
            .card {
                border: 1px solid #ccc; 
                padding: 10px; 
                border-radius: 10px; 
                background: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
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
            // Mostra preview da imagem enviada
            function previewImagem(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById("preview").innerHTML = `
                            <h3>🖼️ Imagem enviada:</h3>
                            <img src="${e.target.result}" alt="Preview" width="200">
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
                                <img src="${item.url}" alt="${item.nome}" width="150"><br>
                                <b>${item.nome}</b><br>
                                Similaridade: ${(item.similaridade * 100).toFixed(1)}%<br>
                                Diferença: ${(item.diferenca * 100).toFixed(1)}%
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
