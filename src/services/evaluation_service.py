import re

class EvaluationService:

    def __init__(self, llm):
        self.llm = llm

    def evaluate_answer(self, question, correct_answer, student_answer):

        prompt = f"""
You are an expert evaluator.

Evaluate the student's answer.

Scoring rules:
- 1 = fully correct
- 0 = completely wrong
- 0.3–0.8 = partial understanding

Question:
{question}

Correct Answer:
{correct_answer}

Student Answer:
{student_answer}

Return STRICTLY in this format:
Score: <number between 0 and 1>
Feedback: <short explanation>

Do NOT add anything else.
"""

        response = self.llm.generate(prompt)

        return self.parse_response(response)

    def parse_response(self, response):
        try:
            score_match = re.search(r"Score:\s*([0-9.]+)", response)
            feedback_match = re.search(r"Feedback:\s*(.*)", response)

            score = float(score_match.group(1)) if score_match else 0
            feedback = feedback_match.group(1).strip() if feedback_match else "No feedback"

            # Clamp score
            score = max(0, min(score, 1))

            return score, feedback

        except Exception:
            return 0, "Evaluation parsing failed"



















































# class EvaluationService:

#     def __init__(self, llm):
#         self.llm = llm

#     def evaluate_answer(self, question, correct_answer, student_answer):
#         prompt = f"""
#         You are an expert evaluator.

#         Evaluate the student's answer based on the correct answer.

#         Question:
#         {question}

#         Correct Answer:
#         {correct_answer}

#         Student Answer:
#         {student_answer}

#         Instructions:
#         - Give a score between 0 and 1
#         - 1 = fully correct
#         - 0 = completely wrong
#         - Partial understanding should get 0.3–0.8
#         - Be strict but fair

#         Output format (STRICT):
#         Score: <number>
#         Feedback: <short explanation>
#         """

#         response = self.llm.generate_text(prompt)

#         return self.parse_response(response)

#     def parse_response(self, response):
#         try:
#             lines = response.split("\n")
#             score = float(lines[0].split(":")[1].strip())
#             feedback = lines[1].split(":", 1)[1].strip()

#             return score, feedback
#         except:
#             return 0, "Evaluation failed"















































# import re

# class EvaluationService:

#     def __init__(self, llm):
#         self.llm = llm

#     def evaluate_answer(self, q, correct, student):

#         prompt = f"""
# Evaluate answer:

# Q: {q}
# Correct: {correct}
# Student: {student}

# Return:
# Score: 0-1
# Feedback:
# """

#         res = self.llm.generate(prompt)

#         try:
#             score = float(re.search(r"Score:\s*([0-9.]+)", res).group(1))
#             feedback = re.search(r"Feedback:\s*(.*)", res).group(1)

#             score = max(0, min(score, 1))

#             return score, feedback

#         except:
#             return 0, "Evaluation failed"