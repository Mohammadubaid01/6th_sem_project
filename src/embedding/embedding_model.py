from sentence_transformers import SentenceTransformer
import numpy as np
from src.config import EMBEDDING_MODEL_NAME

class EMBEDDING:
    def __init__(self, model_name=EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, text):
        embedding = self.model.encode(text)
        return np.array(embedding).astype("float32")

    # def encode(self, text):
    #         embedding = self.model.encode(text)
    #         return np.array(embedding)


    def cosine_similarity(self, vec1, vec2):
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    
    
