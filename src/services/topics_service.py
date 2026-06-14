import re

def detect_topic_llm(llm, question):
    prompt = f"""
You are an academic topic classifier.

Extract the main topic from the question.

Rules:
- Return ONLY one topic
- Maximum 3 words
- No explanations
- No punctuation
- No sentences

Examples:
Question: What is recursion?
Topic: Recursion

Question: Explain normalization in SQL
Topic: DBMS

Question: What is CNN in deep learning?
Topic: Deep Learning

Question:
{question}

Topic:
"""

    response = llm.generate(prompt).strip()

    topic = response.split("\n")[0]

    return normalize_topic(topic) if topic else "General"






def normalize_topic(topic: str):
    topic = topic.strip()

    # Remove labels like "Topic:"
    topic = re.sub(r"^topic\s*:\s*", "", topic, flags=re.IGNORECASE)

    # Remove punctuation at ends
    topic = topic.strip(" .,:;!?-_/")

    # Collapse extra spaces
    topic = " ".join(topic.split())

    # Handle only very common abbreviations
    abbreviations = {
        "os": "Operating Systems",
        "dbms": "DBMS",
        "cn": "Computer Networks",
        "ml": "Machine Learning",
        "ai": "Artificial Intelligence",
        "oop": "Object Oriented Programming",
        "daa": "Design and Analysis of Algorithms"
    }

    lower_topic = topic.lower()

    if lower_topic in abbreviations:
        return abbreviations[lower_topic]

    # Default formatting
    return topic.title()




































