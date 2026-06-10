from src.pipeline.rag_pipeline import RAGPipeline
from src.ingestion.loader import load_file
from src.ingestion.chunker import chunk_text

class QAService:
    def __init__(self):
        self.pipeline = RAGPipeline()

    def process_document(self, file_path):
        text = load_file(file_path)
        chunks = chunk_text(text)
        self.pipeline.ingest(chunks)

    def answer_question(self, question):
        return self.pipeline.answer(question)

