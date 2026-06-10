import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, 'DATA')
MODEL_DIR = os.path.join(BASE_DIR, 'MODELS')

FAISS_INDEX_PATH = os.path.join(MODEL_DIR, 'faiss.index')
CHUNKS_PATH = os.path.join(MODEL_DIR, 'chunks.pkl')

EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


