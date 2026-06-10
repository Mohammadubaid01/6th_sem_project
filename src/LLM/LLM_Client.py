import ollama

class LLMClient:

    def __init__(self):
        self.model = "llama3:8b"

    def generate(self, prompt):
        res = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return res["message"]["content"]


















































# import ollama

# class LLMClient:
#     def __init__(self, model="llama3:8b"): # or you can use "llama3" in model but it is slower
#         self.model = model

#     def generate_response(self, context, question):
#         prompt = f"""
        
        
#         You are an AI Study Assistant.

#         Explain the answer clearly for a student.

#         Instructions:
#         1. Use context as base
#         2. Add additional explanation if needed
#         3. Do NOT copy text
#         4. Explain in simple language
#         5. Add examples
#         6. Do NOT mention "context" or "document"
        
        
        
#         {question}
#         ---------------------
#         Context:
#         {context}
#         ---------------------

        
        

#         Answer:
#         """

#         response = ollama.chat(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             options={
#                 "temperature": 0.2,
#                 "num_predict": 150
#                 }
#         )

#         return response['message']['content']
    
    
#     def generate_text(self, prompt):
#         response = ollama.chat(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             options={
#                 "temperature": 0.2,
#                 "num_predict": 150
#                 }
#         )

#         return response['message']['content']
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
'''from openai import OpenAI
from src.config import OPENAI_API_KEY

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        
    def generate_response(self, context, question):
        
        prompt = f"""
        Answer the following question based on the provided context. 
        If the context does not contain enough information to answer the 
        question, say "I don't know".
        
        Context: {context}
        
        Question: {question}
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()'''