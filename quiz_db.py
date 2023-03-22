import redis

# Establish a connection to the Redis server
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def add_quiz(quiz_name, questions):

    quiz_name = quiz_name.lower()
    # Insert the new quiz into the quizzes set
    r.sadd("quizzes", quiz_name)

    # Insert the questions into the questions hash and associate them with the quiz_name
    for question, answer in questions:
        r.hset(f"quiz:{quiz_name}:questions", question, answer)

    print(f'Quiz "{quiz_name}" added to the database.')


# Example usage
quiz_name = "gen1"
questions = [
    ("What type is Pikachu?", "Electric"),
    ("What is the first Pokémon in the Pokédex?", "Bulbasaur"),
    # Add more questions here
]

add_quiz(quiz_name, questions)
