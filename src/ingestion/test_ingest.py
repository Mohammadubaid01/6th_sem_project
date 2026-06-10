import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

from src.ingestion.loader import load_file
from src.ingestion.chunker import chunk_text

# Paths
BASE_DIR = os.getcwd()
MODEL_DIR = os.path.join(BASE_DIR, "MODELS")

os.makedirs(MODEL_DIR, exist_ok=True)

FAISS_INDEX_PATH = os.path.join(MODEL_DIR, "faiss.index")
CHUNKS_PATH = os.path.join(MODEL_DIR, "chunks.pkl")

# Step 1: Load file
text = load_file("DATA/raw/your_file.pdf")  # change path if needed

# Step 2: Chunk text
chunks = chunk_text(text)

print(f"Total chunks: {len(chunks)}")

# Step 3: Create embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks)

# Step 4: Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Step 5: Save FAISS index
faiss.write_index(index, FAISS_INDEX_PATH)

# Step 6: Save chunks
with open(CHUNKS_PATH, "wb") as f:
    pickle.dump(chunks, f)

print(" Ingestion complete. FAISS index created.")