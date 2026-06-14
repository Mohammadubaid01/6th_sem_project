from src.embedding.embedding_model import EMBEDDING
from src.vector_store.faiss_store import FaissStore
from src.LLM.LLM_Client import LLMClient

from src.services.tracking_service import TrackingService
from src.services.topics_service import detect_topic_llm
from src.services.evaluation_service import EvaluationService

from src.tools.web_search import search_web
from src.prompts.prompt_manager import PromptManager

import time
from datetime import datetime
import json
import re


class RAGPipeline:

    def __init__(self):
        self.vector_store = FaissStore()
        self.embedding_model = EMBEDDING()
        self.llm = LLMClient()
        self.tracker = TrackingService()
        self.evaluator = EvaluationService(self.llm)

    # ---------------- INGEST ----------------
    def ingest(self, file_path, user_id):
        from src.ingestion.loader import load_file
        from src.ingestion.chunker import chunk_text

        text = load_file(file_path)
        chunks = chunk_text(text)

        embeddings = self.embedding_model.encode(chunks)
        self.vector_store.build(embeddings, chunks, user_id)

        return "Document processed successfully"

    # ---------------- RETRIEVE ----------------
    def retrieve(self, query, user_id, top_k=5):
        self.vector_store.load(user_id)

        if self.vector_store.index is None:
            return [], []

        query_vector = self.embedding_model.encode([query])
        
        distances, indices = self.vector_store.index.search(query_vector, top_k)

        results = []
        sims = []

        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.vector_store.chunks):
                results.append(self.vector_store.chunks[idx])
                
                # convert distance → similarity
                sim = 1 / (1 + distances[0][i])
                sims.append(sim)

        return results, sims

    # ---------------- ANSWER + EVALUATION ----------------
    def generate_answer(self, query, user_id, user_answer=None):
        
        self.vector_store.load(user_id)   
        if self.vector_store.index is None:   
            return {
                "answer": "No documents uploaded yet.",
                "score": None,
                "feedback": None
            }

        start_time = time.time()

        # chunks = self.retrieve(query, user_id)
        # pdf_context = "\n\n".join(chunks)
        
        chunks, sims = self.retrieve(query, user_id)

        similarity_score = sum(sims) / len(sims) if sims else 0

        pdf_context = "\n\n".join(chunks) if chunks else ""

        web_context = ""
        if not pdf_context:
            web_context = search_web(query)

        context = pdf_context + "\n\n" + web_context

        web_context = ""
        if not pdf_context:
            web_context = search_web(query)

        context = pdf_context + "\n" + web_context
        
        if pdf_context:
            context_score = 1.0
        else:
            context_score = 0.6   # web fallback less reliable

        student_level = self.tracker.get_student_level(user_id)
        weak_topics = self.tracker.get_weak_topics(user_id)

        prompt = PromptManager.qa_prompt(context, query, student_level, weak_topics)

        correct_answer = self.llm.generate(prompt)

        score = None
        feedback = None
        is_correct = None

        if user_answer:
            score, feedback = self.evaluator.evaluate_answer(
                query,
                correct_answer,
                user_answer
            )
            is_correct = score >= 0.7
            
        confidence = (
            0.5 * similarity_score +
            0.3 * (score if score is not None else 0.5) +
            0.2 * context_score
        )

        topic = detect_topic_llm(self.llm, query)

        self.tracker.save_attempt({
            "user_id": user_id,
            "question": query,
            "topic": topic,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "score": score,
            "feedback": feedback,
            "is_correct": is_correct,
            "time_taken": time.time() - start_time,
            "timestamp": datetime.utcnow()
        })

        return {
            "answer": correct_answer,
            "score": score,
            "feedback": feedback,
            "confidence": round(confidence, 2)
        }

    # ---------------- SUMMARY ----------------
    def summarize(self, user_id, topics=None):

        self.vector_store.load(user_id)

        chunks = self.vector_store.get_all_chunks()

        if topics:
            filtered_chunks = []

            for c in chunks:
                for t in topics:
                    words = t.lower().split()

                    if any(word in c.lower() for word in words):
                        filtered_chunks.append(c)
                        break

            chunks = filtered_chunks

        if not chunks:
            return "No related content found in uploaded documents."

        context = "\n\n".join(chunks[:10])

        prompt = f"""
        Summarize the following content clearly for students:

        {context}
        """

        return self.llm.generate(prompt)

    # ---------------- QUESTION GENERATION ----------------
    def generate_questions(self, user_id, num=5):
        self.vector_store.load(user_id)

        chunks = self.vector_store.get_all_chunks()
        context = "\n\n".join(chunks[:10])

        prompt = PromptManager.question_generation_prompt(context, num)

        return self.llm.generate(prompt)

    # ---------------- MCQ ----------------
    def generate_mcqs(self, user_id, num=4):
        self.vector_store.load(user_id)

        chunks = self.vector_store.get_all_chunks()
        context = "\n\n".join(chunks[:3])

        prompt = PromptManager.mcq_prompt(context, num)

        response = self.llm.generate(prompt)

        mcqs = self.safe_json_load(response)

        if not mcqs:
            return [{"error": "Failed to generate MCQs. Try again."}]

        return mcqs

    # ---------------- MSQ ----------------
    def generate_msqs(self, user_id, num=4):
        self.vector_store.load(user_id)

        chunks = self.vector_store.get_all_chunks()
        context = "\n\n".join(chunks[:3])

        prompt = PromptManager.msq_prompt(context, num)

        response = self.llm.generate(prompt)

        mcqs = self.safe_json_load(response)

        if not mcqs:
            return [{"error": "Failed to generate MCQs. Try again."}]

        return mcqs
        
        
    





    def safe_json_load(self, text):
        try:
            text = text.strip()

            # remove markdown
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)

            # find first JSON array
            start = text.find("[")
            end = text.rfind("]") + 1

            if start == -1 or end == 0:
                return []

            text = text[start:end]

            data = json.loads(text)

            # ensure list
            if isinstance(data, dict):
                data = [data]

            return data

        except Exception as e:
            print("JSON Error:", e)
            print("RAW RESPONSE:\n", text)
            return []

    



















