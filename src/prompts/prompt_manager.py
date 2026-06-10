class PromptManager:

    @staticmethod
    def qa_prompt(context, query, level, weak):
        return f"""
Level: {level}
Weak Topics: {weak}

Context:
{context}

Question:
{query}

Answer clearly with explanation and examples.
"""

    @staticmethod
    def mcq_prompt(context, num):
        return f"""
Generate {num} MCQs from the given context.

Return ONLY valid JSON.

Format:
[
  {{
    "question": "What is DBMS?",
    "options": {{
      "A": "Database Management System",
      "B": "Digital Base Management System",
      "C": "Data Backup Management System",
      "D": "None"
    }},
    "answer": "A",
    "explanation": "DBMS stands for Database Management System."
  }}
]

Context:
{context}
"""

    @staticmethod
    def msq_prompt(context, num):
        return f"""
Generate exactly {num} Multiple Select Questions (MSQs).

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answers": ["A", "C"],
    "explanation": "Explanation here"
  }}
]

Rules:
- Return ONLY JSON
- No markdown
- No ```json
- No explanation outside JSON
- Each question must have multiple correct answers
- answers must be an array

Context:
{context}
"""

    @staticmethod
    def question_generation_prompt(context, num):
        return f"""
Generate {num} important questions from the given context.

Context:
{context}
"""




















































# class PromptManager:

#     @staticmethod
#     def qa_prompt(context, query, level, weak):
#         return f"""
# Level: {level}
# Weak: {weak}

# Context:
# {context}

# Question:
# {query}

# Answer clearly with explanation and examples.
# """

#     @staticmethod
#     def mcq_prompt(context, num):
#         return f"""Generate {num} MCQs in JSON... {context}"""

#     @staticmethod
#     def msq_prompt(context, num):
#         return f"""Generate {num} MSQs in JSON... {context}"""

#     @staticmethod
#     def question_generation_prompt(context, num):
#         return f"""Generate {num} questions... {context}"""