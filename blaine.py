import os
import sys
import random
import discord
from discord.ext import commands
from discord.utils import get
import dotenv
from dotenv import load_dotenv
from quiz_db import add_quiz
import redis
import asyncio

LOCK_FILE = 'blaine.lock'

# Check if the lock file exists
if os.path.exists(LOCK_FILE):
    print("Another instance the blaine-bot is running. Exiting...")
    sys.exit(1)

# Create the lock file
with open(LOCK_FILE, 'w') as lock_file:
    lock_file.write('1')

load_dotenv()

# Set up the bot with a prefix for commands, e.g., !quiz
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load your Discord bot token
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# Establish a connection to the Redis server
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='add_quiz', help='Adds a new quiz. Usage: !add_quiz <quiz_name>;<question>;<answer>|<question>;<answer>|...')
@commands.has_permissions(administrator=True)
async def add_quiz_command(ctx, *, quiz_data: str):
    # Split the input string into quiz_name and questions
    quiz_name, question_data = quiz_data.split(';', 1)
    question_data = question_data.split('|')

    # Parse the questions
    questions = [tuple(q.split(';', 1)) for q in question_data]

    # Call the add_quiz function
    add_quiz(quiz_name.strip(), questions)

    await ctx.send(f'Quiz "{quiz_name.strip()}" added successfully.')


@bot.command(name='start_quiz', help='Starts a quiz. Usage: !start_quiz <quiz_name>')
async def start_quiz(ctx, quiz_name: str):
    quiz_name = quiz_name.lower()

    print(f"Searching for quiz: {quiz_name}")  # Debug print statement

    if not r.sismember("quizzes", quiz_name):
        all_quizzes = r.smembers("quizzes")
        # Debug print statement
        print(f"Available quizzes in Redis: {all_quizzes}")
        await ctx.send("Quiz not found.")
        return

    questions = r.hgetall(f"quiz:{quiz_name}:questions")
    questions = list(questions.items())
    random.shuffle(questions)

    correct = 0

    for index, (question, answer) in enumerate(questions):
        await ctx.send(f'Question {index+1}: {question}')
        await asyncio.sleep(0.5)
        response = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)

        if response.content.lower() == answer.lower():
            correct += 1
            await ctx.send("Correct!")
        else:
            await ctx.send(f"Wrong. The correct answer is: {answer}")

    await ctx.send(f'You answered {correct} out of {len(questions)} questions correctly.')
    await award_role(ctx, correct, len(questions))


async def award_role(ctx, correct, total_questions):
    percentage = correct / total_questions * 100

    if percentage >= 80:
        role_name = 'Pokémon Master'
    elif percentage >= 50:
        role_name = 'Pokémon Trainer'
    else:
        role_name = 'Beginner Trainer'

    role = get(ctx.guild.roles, name=role_name)

    if not role:
        role = await ctx.guild.create_role(name=role_name)

    await ctx.author.add_roles(role)
    await ctx.send(f'You have been awarded the {role_name} role.')


bot.run(TOKEN)

# Remove the lock file before exiting
os.remove(LOCK_FILE)
