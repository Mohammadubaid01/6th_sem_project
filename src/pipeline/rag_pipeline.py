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

    














































































# from src.embedding.embedding_model import EMBEDDING
# from src.vector_store.faiss_store import FaissStore
# from src.LLM.LLM_Client import LLMClient


# from src.ingestion.loader import load_file
# from src.ingestion.chunker import chunk_text

# from src.services.tracking_service import TrackingService
# from src.services.topics_service import detect_topic_llm
# from src.tools.web_search import search_web
# from src.services.evaluation_service import EvaluationService
# import time
# from datetime import datetime

# import faiss
# import pickle
# import os

# from src.config import FAISS_INDEX_PATH, CHUNKS_PATH


# class RAGPipeline:
#     def __init__(self):
#         self.vector_store = FaissStore()
#         self.embedding_model = EMBEDDING()
#         self.llm = LLMClient()
#         self.tracker = TrackingService()
#         self.evaluator = EvaluationService(self.llm)

#         # # Try loading existing index (if exists)
#         # self.vector_store.load()

#     #  INGEST (THIS IS THE CORRECT PLACE)
#     def ingest(self, file_path, user_id):
#         text = load_file(file_path)
#         chunks = chunk_text(text)

#         embeddings = self.embedding_model.encode(chunks)

#         self.vector_store.build(embeddings, chunks, user_id)
#         return " Document processed successfully"

#     #  retrieve the relevant chunks from FAISS index
#     def retrieve(self, query, user_id, top_k=5):
#         # self.vector_store.load(user_id)
#         if self.vector_store.index is None:
#             return []

#         query_vector = self.embedding_model.encode([query])
#         return self.vector_store.search(query_vector, top_k)

#     #  generate answer using the retrieved chunks + webdata + personalisation

#     def generate_answer(self, query, user_id, user_answer=None, top_k=3):
#         self.vector_store.load(user_id)

#         start_time = time.time()

#         # Retrieve the PDF chunks
#         retrieved_chunks = self.retrieve(query, user_id, top_k)

#         pdf_context = ""
#         if retrieved_chunks:
#             pdf_context = "\n\n".join(retrieved_chunks)

#         # # Get the web data (ALWAYS try to get web data, even if PDF data exists. It can enhance the answer)
#         # web_context = search_web(query)
        
#         web_context = ""
#         if not pdf_context:
#             web_context = search_web(query)

         
#         if not pdf_context and not web_context:
#             return "No relevant information found."

#         # Combine contexts with smart prompt 
#         combined_context = f"""
        
#         {pdf_context}

        
#         {web_context}
#         """
        
#         # Personalization step: Get student level and weak topics from tracking service
#         student_level = self.tracker.get_student_level(user_id)
#         weak_topics = self.tracker.get_weak_topics(user_id)
        
#         recent_chats = self.tracker.get_recent_chats(user_id)

#         memory_context = ""
#         for q, a in recent_chats:
#             memory_context += f"User: {q}\nAssistant: {a}\n\n"

#         # Smart prompt with instructions for the LLM 
#         prompt = f"""
#         You are an advanced AI Study Assistant.
        
#         Your job is to give a WELL-STRUCTURED answer.

#         Student Level: {student_level}
        
#         Conversation History: {memory_context}

#         Use BOTH sources:
#         1. PDF Content (user notes)
#         2. Web Content (latest knowledge)

#         Adapt your explanation based on student level:

#         - If beginner:
#         -> Use very simple language
#         -> Explain step-by-step
#         -> Use basic examples

#         - If intermediate:
#         -> Moderate explanation
#         -> Include reasoning

#         - If advanced:
#         -> Deep technical explanation
#         -> Include optimizations and edge cases

#         Focus more explanation on these weak topics if relevant:
#         {weak_topics}
        
#         Follow STRICT format:

#         Definition:
#         <short definition>

#         Explanation:
#         <clear explanation>
#         <if asked for a concept, detailed explanation>

#         Key Points:
#         - point 1
#         - point 2
#         - point 3

#         Example:
#         <if applicable>

#         Formatting rules:
#         - Use proper headings
#         - Use bullet points (• or -)
#         - Keep spacing clean
#         - Avoid long paragraphs
#         - Make it easy to read and understand
        
#         WRITING RULES:
#         - Avoid storytelling
#         - Be direct and structured
#         - Do NOT use phrases like "Let's start", "Imagine", "Think of"
#         - Do NOT add unnecessary introductions

#         Instructions:
#         - If PDF content exists, prioritize it
#         - Use web content to enhance or fill gaps
#         - If no PDF content, rely fully on web
#         - Explain clearly and in a structured way
#         - Add examples if helpful
#         - Do NOT mention "PDF", "web", or "sources"

#         Question:
#         {query}
#         """
        

#         # Generate answer using LLM with the combined context and personalization  
#         correct_answer = self.llm.generate_response(combined_context, prompt)

#         # Evaluation of student's answer (in hybrid model, we can evaluate the student's answer against the correct answer generated by LLM. This provides immediate feedback to the student and helps in adaptive learning.)
#         is_correct = None
#         score = 0
#         feedback = None

#         if user_answer:
#             score, feedback = self.evaluator.evaluate_answer(
#                 query,
#                 correct_answer,
#                 user_answer
#             )

#             is_correct = score >= 0.7

#         # Topic detection (LLM)
#         topic = detect_topic_llm(self.llm, query)
        
#         end_time = time.time()

#         # Save attempt (MongoDB) 
#         attempt = {
#             "user_id": user_id,
#             "question": query,
#             "topic": topic,
#             "difficulty": "medium",
#             "question_type": "subjective",
#             "user_answer": user_answer,
#             "correct_answer": correct_answer,
#             "is_correct": is_correct,
#             "score": score,
#             "feedback": feedback,
#             "time_taken": end_time - start_time,
#             "repeated": False,
#             "timestamp": datetime.utcnow()
#         }

#         self.tracker.save_attempt(attempt)

#         return correct_answer

#     #  FINAL API FUNCTION
#     def answer(self, question, user_id, top_k=5):
        
#         self.vector_store.load(user_id)
        
#         if self.vector_store.index is None:
#             return "No documents uploaded yet."

#         return self.generate_answer(question, user_id, top_k)


  
#     def summarize(self, user_id, top_k=10):
#     # this line ensure vector store is loaded
#         self.vector_store.load(user_id)

        
#         chunks = self.vector_store.get_all_chunks()

#         if not chunks:
#             return "No document available to summarize. Please upload a file first."

#         # limit chunks, it avoid token overflow
#         selected_chunks = chunks[:top_k]

#         # combine chunks into context
#         context = "\n\n".join(selected_chunks)

#         # Prompt for summarization
#         prompt = """
#     You are an AI Study Assistant.

#     Generate a clear and structured summary for a student.

#     Instructions:
#     1. Do NOT copy text directly
#     2. Explain in simple language
#     3. Include key concepts
#     4. Add short explanations
#     5. Make it useful for revision

#     Give output in:
#     - Bullet points
#     - Short paragraphs

#     """

#         # call LLM to generate summary
#         response = self.llm.generate_response(context, prompt)

#         return response
    
    
    
    
    
#     def generate_questions(self, user_id, num_questions=10, top_k=10):
        
#         self.vector_store.load(user_id)

#         chunks = self.vector_store.get_all_chunks()

#         if not chunks:
#             return "No document available. Please upload a file first."

#         # limit questions between 1–20
#         if num_questions < 1 or num_questions > 20:
#             return "Number of questions must be between 1 and 20."

        
#         selected_chunks = chunks[:top_k]
#         context = "\n\n".join(selected_chunks)

#         # prompt for question generation
#         prompt = f"""
#     You are an AI teacher.

#     Generate {num_questions} questions from the given content.

#     IMPORTANT REQUIREMENTS:

#     1. Include a MIX of question types:
#     - Conceptual
#     - Numerical / Problem-solving
#     - Application-based
#     - Exam-level

#     2. Include a MIX of difficulty:
#     - Easy
#     - Medium
#     - Hard

#     3. Do NOT copy text directly

#     4. Questions must be clear and useful for students

#     5. Do NOT include answers

#     6. Clearly label each question like:
#     [Type: Conceptual | Difficulty: Easy]

#     Output format:

#     1. [Type: ... | Difficulty: ...] Question...
#     2. [Type: ... | Difficulty: ...] Question...
#     ...
    
#     - Output must STRICTLY follow format
#     - If format is broken, regenerate internally

#     Content:
#     {context}
#     """

#         response = self.llm.generate_text(prompt)

#         return response
    
    
    
#     def generate_quiz(self, user_id, num_questions=5, top_k=10):
        
#         self.vector_store.load(user_id)

#         chunks = self.vector_store.get_all_chunks()

#         if not chunks:
#             return "No document available. Please upload a file first."

#         # limit questions between 1–20
#         if num_questions < 1 or num_questions > 20:
#             return "Number of questions must be between 1 and 20."

        
#         selected_chunks = chunks[:top_k]
#         context = "\n\n".join(selected_chunks)

#         # Prompt for quiz generation (MCQs)
#         prompt = f"""
#     You are an AI exam generator.

#     Generate {num_questions} multiple choice questions (MCQs) from the given content.
    
#     STRICT RULES:
#     - ONLY generate MCQs
#     - DO NOT explain anything outside format
#     - DO NOT write paragraphs
#     - DO NOT behave like a tutor


#     Instructions:

#     1. Each question must have 4 options (A, B, C, D)
#     2. Only ONE correct answer
#     3. Include explanation for the correct answer
#     4. Questions must be a mix of:
#     - Conceptual
#     - Numerical
#     - Application-based
#     5. Difficulty should be mixed (easy, medium, hard)
#     6. Do NOT copy text directly

#     Output format:

#     Q1. Question text
#     A. Option
#     B. Option
#     C. Option
#     D. Option
#     Answer: Options having correct answer, could be any options from A to D but only the correct one is mentioned
#     Explanation: ...

#     Q2. ...
    
#     - Output must STRICTLY follow format
#     - If format is broken, regenerate internally

#     Content:
#     {context}
#     """

#         response = self.llm.generate_text(prompt)

#         return response











# def safe_json_load(self, text):
    #     try:
    #         text = text.replace("```json", "").replace("```", "").strip()

    #         start = text.find("[")
    #         end = text.rfind("]") + 1

    #         if start == -1 or end == 0:
    #             return []

    #         return json.loads(text[start:end])
    #     except:
    #         return []


















# def summarize(self, top_k=10):
#     self.vector_store.load()

#     # get stored chunks
#     chunks = self.vector_store.get_all_chunks()

#     # limit chunks
#     selected_chunks = chunks[:top_k]

#     context = "\n\n".join(selected_chunks)

#     prompt = f"""
#     Summarize the following content in a clear and structured way.

#     Include:
#     - key concepts
#     - important points
#     - short explanations

#     Content:
#     {context}
#     """

#     return self.llm.generate_response(context, prompt)



































# from src.embedding.embedding_model import EMBEDDING
# from src.vector_store.faiss_store import FaissStore
# from src.LLM.LLM_Client import LLMClient


# class RAGPipeline:
#     def __init__(self):
#         self.vector_store = FaissStore()
#         self.vector_store.load()
#         self.embedding_model = EMBEDDING()
#         self.llm = LLMClient()
#         # self.vector_store.load()  # load once

#     # Build + Store FAISS index
#     def ingest(self, chunks):
#         embeddings = self.embedding_model.encode(chunks)
#         self.vector_store.build(embeddings, chunks)

#     # Load FAISS index 
#     def load(self): # faiss index should be loadeed before retrieval, its very important
#         self.vector_store.load()

    
#     # 
    
    
#     def retrieve(self, query, top_k=5):
#         if self.vector_store.index is None:
#             self.vector_store.load()

#         query_vector = self.embedding_model.encode([query])
#         return self.vector_store.search(query_vector, top_k)

    
#     def generate_answer(self, query, top_k=5):
#         retrieved_chunks = self.retrieve(query, top_k)
#         context = "\n\n".join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(retrieved_chunks)])
#         answer = self.llm.generate_response(context, query)
#         return answer



    # def generate_answer(self, query, user_id, top_k=5):
    #     retrieved_chunks = self.retrieve(query, user_id, top_k)

    #     if not retrieved_chunks:
    #         return "No documents uploaded yet."

    #     context = "\n\n".join(retrieved_chunks)

    #     return self.llm.generate_response(context, query)

   
#     def answer(self, question, top_k=5):
#         if self.vector_store.index is None:
#             self.vector_store.load()

#         if self.vector_store.index is None:
#             return "Please upload a PDF first."

#         return self.generate_answer(question, top_k)