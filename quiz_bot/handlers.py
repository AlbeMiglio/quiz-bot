import re

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler

INIT, CUSTOM_NQ, QUIZ = range(3)

BUTTONS = {
    "quick_quiz": "Quiz rapido - 5",
    "exam_sim31": "Vecchio Esame - 31",
    "exam_sim33": "Esame 24/25 - 33",
    "set_nq": "Imposta numero domande",
}

def get_main_menu_keyboard():
    """
    Costruisce la tastiera dinamica per il menu iniziale (INIT).
    """
    button_labels = [[label] for label in BUTTONS.values()]
    return ReplyKeyboardMarkup(button_labels, one_time_keyboard=True, resize_keyboard=True)

def build_main_conversation(bot_instance):
    """
    Definisce il flusso di conversazione con i nuovi stati.
    """
    button_labels_regex = f"^({'|'.join(BUTTONS.values())})$"

    return ConversationHandler(
        entry_points=[CommandHandler('start', bot_instance.start_command),
                      MessageHandler(Filters.regex(button_labels_regex), bot_instance.handle_button_press)],
        states={
            INIT: [
                MessageHandler(Filters.regex(button_labels_regex), bot_instance.handle_button_press),
            ],
            CUSTOM_NQ: [
                MessageHandler(Filters.text & ~Filters.command, bot_instance.choose_number_of_questions),
            ],
            QUIZ: [
                MessageHandler(Filters.regex(r"^(A|B|C|D|E|F|Skip|Cancel)$"), bot_instance.quiz_ans),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("Cancel"), bot_instance.cancel_quiz)],
        name="quiz_bot_conversation",
        persistent=True,
        allow_reentry=True
    )


def make_keyboard_for_question(num_options: int, row_size: int = 2) -> ReplyKeyboardMarkup:
    """
    Crea una tastiera dinamica per il quiz con N bottoni + Skip e Cancel.
    """
    letters = [chr(ord('A') + i) for i in range(num_options)]

    rows = [letters[i:i + row_size] for i in range(0, len(letters), row_size)]

    rows.append(["Skip", "Cancel"])

    return ReplyKeyboardMarkup(rows, one_time_keyboard=True, resize_keyboard=True)