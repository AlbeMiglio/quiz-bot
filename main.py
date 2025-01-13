from quiz_bot.bot_runner import NetworkQuizBot
from os import environ

def main():
    token = environ.get("QUIZ_BOT_TOKEN")
    questions_json_path = "questions.json"

    bot = NetworkQuizBot(token, questions_json_path)
    bot.start_bot()

if __name__ == "__main__":
    main()