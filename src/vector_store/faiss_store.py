import faiss
import pickle
import numpy as np
import os
from src.config import FAISS_INDEX_PATH, CHUNKS_PATH


class FaissStore:
    def __init__(self):
        self.index = None
        self.chunks = None

    def build(self, vectors, chunks, user_id):
        
        user_dir = os.path.join("MODELS", f"user_{user_id}")

        os.makedirs(user_dir, exist_ok=True)

        faiss_path = os.path.join(user_dir, "faiss.index")
        chunks_path = os.path.join(user_dir, "chunks.pkl")
        
        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(vectors)

        # Save index
        faiss.write_index(self.index, faiss_path)

        # Save chunks
        with open(chunks_path, 'wb') as f:
            pickle.dump(chunks, f)

        self.chunks = chunks  # keep in memory

        print(" FAISS index built for {user_id} and saved")

    def load(self, user_id):
        try:
            
            user_dir = os.path.join("MODELS", f"user_{user_id}")

            faiss_path = os.path.join(user_dir, "faiss.index")

            chunks_path = os.path.join(user_dir, "chunks.pkl")
            if os.path.exists(faiss_path) and os.path.exists(chunks_path):
                self.index = faiss.read_index(faiss_path)

                with open(chunks_path, "rb") as f:
                    self.chunks = pickle.load(f)

                print(" FAISS index + chunks loaded")

            else:
                print(" No FAISS index found. Waiting for upload...")
                self.index = None
                self.chunks = []

        except Exception as e:
            print(" Error loading FAISS:", e)
            self.index = None
            self.chunks = []
    
    
    
    

    # def load(self):
    #     if os.path.exists(FAISS_INDEX_PATH):
    #         self.index = faiss.read_index(FAISS_INDEX_PATH)
    #     else:
    #         print(" No FAISS index found. Waiting for upload...")
    #         self.index = None

    def search(self, query_vector, top_k=5):
        if self.index is None or self.chunks is None:
            raise ValueError("FaissStore not loaded. Upload PDF first.")

        # FIX: correct shape
        query_vector = np.array(query_vector).astype('float32')

        distances, indices = self.index.search(query_vector, top_k)
        similarity = 1 / (1 + distances[0][0])  # simple similarity score

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])

        return results

    def get_all_chunks(self):
        if self.chunks is None:
            raise ValueError("Chunks not loaded.")
        return self.chunks
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    








