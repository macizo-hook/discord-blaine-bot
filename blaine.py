import os
import sys
import random
import discord
from discord.ext import commands
from discord.utils import get
import dotenv
from dotenv import load_dotenv
import redis
import asyncio
from quiz_mgr import QuizManager, load_quizzes_from_file

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

# Instantiate the QuizManager
quiz_manager = QuizManager(r)

# Load quizzes from the JSON file
load_quizzes_from_file("quizzes.json", quiz_manager)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='add_quiz', help='Adds a new quiz. Usage: !add_quiz <quiz_name>;<question>;<answer>;<option1>;<option2>;<option3>|...')
@commands.has_permissions(administrator=True)
async def add_quiz_command(ctx, *, quiz_data: str):
    quiz_name, question_data = quiz_data.split(';', 1)
    question_data = question_data.split('|')

    # Parse the questions
    questions = [tuple(q.split(';')) for q in question_data]
    formatted_questions = [(q[0], q[1], q[2:]) for q in questions]

    # Call the add_quiz method from the QuizManager instance
    quiz_manager.add_quiz(quiz_name.strip(), formatted_questions)

    await ctx.send(f'Quiz "{quiz_name.strip()}" added successfully.')


@bot.command(name='start_quiz', help='Starts a quiz. Usage: !start_quiz <quiz_name>')
async def start_quiz(ctx, quiz_name: str):
    if not quiz_manager.quiz_exists(quiz_name):
        all_quizzes = quiz_manager.get_all_quizzes()
        await ctx.send("Quiz not found.")
        return

    questions = quiz_manager.get_quiz(quiz_name)
    random.shuffle(questions)

    correct = 0

    for index, (question, (answer, options)) in enumerate(questions):
        options_text = '\n'.join(
            [f"{i+1}. {option}" for i, option in enumerate(options)])
        await ctx.send(f'Question {index+1}: {question}\n\n{options_text}')

        await asyncio.sleep(0.5)
        response = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
        # cast to int to compare the user's response to the correct answer's index.
        if int(response.content) == options.index(answer.lower()) + 1:
            correct += 1
            await ctx.send("Correct!")
        else:
            await ctx.send(f"Wrong. The correct answer is: {answer}")

    await ctx.send(f'You answered {correct} out of {len(questions)} questions correctly.')
    await award_role(ctx, correct, len(questions))


async def award_role(ctx, correct, total_questions):
    percentage = correct / total_questions * 100

    try:
        if percentage >= 80:
            role_name = 'Pokémon Master'
        elif percentage >= 50:
            role_name = 'Pokémon Trainer'
        else:
            role_name = 'Beginner Trainer'

    except Exception as error:
        print("some error happened!", str(error))
        exit()

    else:
        role = get(ctx.guild.roles, name=role_name)

        if not role:
            role = await ctx.guild.create_role(name=role_name)

        await ctx.author.add_roles(role)
        await ctx.send(f'You have been awarded the {role_name} role.')


bot.run(TOKEN)

# Remove the lock file before exiting
os.remove(LOCK_FILE)
