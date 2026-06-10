from src.database.mongo_db import attempts_collection
from src.database.db import get_connection  

class TrackingService:

    def save_attempt(self, attempt):
        attempts_collection.insert_one(attempt)

    def analyze_performance(self, user_id):
        user_data = list(attempts_collection.find({"user_id": user_id}))

        topic_stats = {}

        for entry in user_data:
            topic = entry.get("topic", "General")

            if topic not in topic_stats:
                topic_stats[topic] = {
                    "correct": 0,
                    "total": 0,
                    "avg_time": 0,
                    "attempts": 0
                }

            topic_stats[topic]["total"] += 1
            topic_stats[topic]["attempts"] += 1

            if entry.get("is_correct"):
                topic_stats[topic]["correct"] += 1

            topic_stats[topic]["avg_time"] += entry.get("time_taken", 0)

        for topic in topic_stats:
            stats = topic_stats[topic]
            stats["accuracy"] = stats["correct"] / stats["total"]
            stats["avg_time"] /= stats["attempts"]

        return topic_stats

    def get_weak_topics(self, user_id, threshold=0.5):
        stats = self.analyze_performance(user_id)

        return [
            topic for topic, data in stats.items()
            if data["accuracy"] < threshold
        ]

    def get_frequent_topics(self, user_id):
        user_data = list(attempts_collection.find({"user_id": user_id}))

        freq = {}

        for entry in user_data:
            topic = entry.get("topic", "General")
            freq[topic] = freq.get(topic, 0) + 1

        return sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    
    
    def get_student_level(self, user_id):
        stats = self.analyze_performance(user_id)

        if not stats:
            return "beginner"

        avg_accuracy = sum(topic["accuracy"] for topic in stats.values()) / len(stats)

        if avg_accuracy < 0.4:
            return "beginner"
        elif avg_accuracy < 0.7:
            return "intermediate"
        else:
            return "advanced"
        
        
        
        
    

    def get_recent_chats(self, user_id, limit=5):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT question, answer
            FROM chats
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return rows[::-1]  # oldest → newest