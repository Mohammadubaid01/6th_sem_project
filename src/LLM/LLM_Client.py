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









































