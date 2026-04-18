import torch
from typing import List
from transformers import AutoTokenizer, AutoModel
from core.config import Emb_conf
class Embedder:
    def __init__(self, config: Emb_conf = Emb_conf()):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        self.model = AutoModel.from_pretrained(config.model_name).to(self.device)

        self.max_token = config.max_token


    def get_embedding(self, text: str) -> List[float]:
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings[0].tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.tolist()