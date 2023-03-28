import redis
import json


class QuizManager:

    def __init__(self, redis_conn):
        self.redis = redis_conn

    def add_quiz(self, quiz_name, questions):
        quiz_name = quiz_name.lower()
        self.redis.sadd("quizzes", quiz_name)
        for question, answer, options in questions:
            self.redis.hset(f"quiz:{quiz_name}:questions",
                            question, json.dumps((answer, options)))

    def get_quiz(self, quiz_name):
        quiz_name = quiz_name.lower()
        if not self.redis.sismember("quizzes", quiz_name):
            return None

        questions = self.redis.hgetall(f"quiz:{quiz_name}:questions")
        if questions:
            questions = [(question, eval(answer_and_options))
                         for question, answer_and_options in questions.items()]
        else:
            questions = []

        return questions

    def get_all_quizzes(self):
        return self.redis.smembers("quizzes")

    def quiz_exists(self, quiz_name):
        return self.redis.sismember("quizzes", quiz_name.lower())


def load_quizzes_from_file(file_path, quiz_manager):
    with open(file_path, 'r') as f:
        quiz_data = json.load(f)
    for quiz_name, questions in quiz_data.items():
        formatted_questions = [(q["question"], q["answer"], [
                                opt.lower() for opt in q["options"]]) for q in questions]
        quiz_manager.add_quiz(quiz_name, formatted_questions)
