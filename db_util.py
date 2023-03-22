import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Remove quizes from the Redis set
r.srem("quizzes", "*")
