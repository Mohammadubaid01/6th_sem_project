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



















































