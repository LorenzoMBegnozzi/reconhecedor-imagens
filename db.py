import pymongo
from bson.binary import Binary

try:
    client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ Conectado ao MongoDB com sucesso!")
except Exception as e:
    print("❌ Erro ao conectar ao MongoDB:", e)

db = client["hotwheels"]
col = db["hotwheels"]

