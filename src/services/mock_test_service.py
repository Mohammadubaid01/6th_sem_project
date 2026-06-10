from datetime import datetime
from src.database.mongo_db import test_results_collection
import json

class MockTestService:

    def __init__(self, llm):
        self.llm = llm



    def generate_mcqs(self, topic, difficulty="medium", num_questions=5):
        prompt = f"""
        Generate {num_questions} MCQs on topic: {topic}
        Difficulty: {difficulty}

        Return ONLY valid JSON in this exact format:

        [
        {{
            "question": "string",
            "options": {{
            "A": "string",
            "B": "string",
            "C": "string",
            "D": "string"
            }},
            "answer": "A",
            "explanation": "string"
        }}
        ]

        Rules:
        - Do NOT include anything outside JSON
        - Ensure valid JSON (no trailing commas)
        """

        response = self.llm.generate_text(prompt)

        # Try JSON first
        mcqs = self.parse_mcqs_json(response)

        # Fallback to old parser if JSON fails
        if not mcqs:
            # print("⚠️ Falling back to text parser...")
            # mcqs = self.parse_mcqs(response)
            raise ValueError("LLM did not return valid JSON")

        return mcqs
        
    
    
    def parse_mcqs(self, text):
        questions = []
        blocks = text.split("Q")

        for block in blocks:
            if not block.strip():
                continue

            try:
                lines = block.strip().split("\n")

                question = lines[0][2:].strip()

                options = {
                    "A": lines[1][3:].strip(),
                    "B": lines[2][3:].strip(),
                    "C": lines[3][3:].strip(),
                    "D": lines[4][3:].strip()
                }

                answer = lines[5].split(":")[1].strip()
                explanation = lines[6].split(":", 1)[1].strip()

                questions.append({
                    "question": question,
                    "options": options,
                    "answer": answer,
                    "explanation": explanation
                })

            except:
                continue

        return questions
    
    
    

    # def parse_mcqs_json(self, response):
    #     try:
    #         cleaned = response.strip().replace("```json", "").replace("```", "")
    #         return json.loads(cleaned)
    #     except:
    #         return []
    
    
    def parse_mcqs_json(self, response):
        try:
            cleaned = response.strip()

            # Remove markdown fences
            cleaned = cleaned.replace("```json", "").replace("```", "")

            # Extract only JSON part
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON array found")

            json_str = cleaned[start:end]

            data = json.loads(json_str)

            # Basic validation
            if isinstance(data, list) and all("question" in q for q in data):
                return data

            return []

        except Exception as e:
            print("JSON parsing failed:", e)
            return []
    
    
    def evaluate_mcq(self, questions, user_answers):
        score = 0
        results = []

        for i, q in enumerate(questions):
            correct = q["answer"]
            user_ans = user_answers[i]

            is_correct = correct == user_ans

            if is_correct:
                score += 1

            results.append({
                "question": q["question"],
                "correct_answer": correct,
                "user_answer": user_ans,
                "is_correct": is_correct,
                "explanation": q["explanation"]
            })

        return score, results
    
    
    def get_adaptive_difficulty(self, user_id, tracker):
        stats = tracker.analyze_performance(user_id)

        if not stats:
            return "easy"  # new user

        avg_accuracy = sum(t["accuracy"] for t in stats.values()) / len(stats)

        if avg_accuracy < 0.4:
            return "easy"
        elif avg_accuracy < 0.7:
            return "medium"
        else:
            return "hard"
        
    

    def save_test_result(self, user_id, topic, score, total, difficulty, time_taken):
        result = {
            "user_id": user_id,
            "topic": topic,
            "score": score,
            "total": total,
            "difficulty": difficulty,
            "time_taken": time_taken,
            "timestamp": datetime.utcnow()
        }

        test_results_collection.insert_one(result)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # def get_adaptive_difficulty(self, user_id, tracker):
    #     weak_topics = tracker.get_weak_topics(user_id)

    #     if weak_topics:
    #         return "easy"   # start easy for weak areas
    #     else:
    #         return "medium"
        
        
    
    