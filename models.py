from pydantic import BaseModel
from typing import List, Optional

class Comparacao(BaseModel):
    nome: str
    url: Optional[str] = None
    similaridade: float
    diferenca: float

class Resultado(BaseModel):
    status: str
    mensagem: str
    top3: List[Comparacao] = []
