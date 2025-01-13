from telegram import Update
from telegram.ext import Updater, CallbackContext, PicklePersistence, CommandHandler, ConversationHandler

from .quiz_manager import QuizManager
from .handlers import build_main_conversation, get_main_menu_keyboard, make_keyboard_for_question, BUTTONS, INIT, CUSTOM_NQ, QUIZ

class NetworkQuizBot:
    def __init__(self, token, questions_json_path):
        self.token = token
        self.quiz_manager = QuizManager(questions_json_path)

        # Persistence per mantenere lo stato del bot
        self.persistence = PicklePersistence(filename='quiz_bot_data')

        # Updater con persistence
        self.updater = Updater(token=self.token, persistence=self.persistence, use_context=True)

    def start_bot(self):
        """
        Avvia il bot e registra gli handler.
        """
        dp = self.updater.dispatcher

        # Aggiungiamo il gestore principale della conversazione
        dp.add_handler(build_main_conversation(self))

        self.updater.start_polling()
        print("Bot avviato!")
        self.updater.idle()

    def start_command(self, update: Update, context: CallbackContext):
        """
        Messaggio di benvenuto con tastiera dinamica.
        """
        update.message.reply_text(
            "Benvenuto! Scegli un'opzione per iniziare:",
            reply_markup=get_main_menu_keyboard()
        )
        return INIT

    def handle_button_press(self, update, context):
        """
        Gestisce i bottoni premuti nel menu principale.
        """
        selected_button = update.message.text
        action_map = {v: k for k, v in BUTTONS.items()}

        action = action_map.get(selected_button)

        if action == "quick_quiz":
            self._start_quiz_for_user(update, context, 5)
            return QUIZ
        elif action == "exam_sim31":
            self._start_quiz_for_user(update, context, 31)
            return QUIZ
        elif action == "exam_sim33":
            self._start_quiz_for_user(update, context, 33)
            return QUIZ
        elif action == "set_nq":
            self.reply_to_choose_nq(update, context)
            return CUSTOM_NQ
        else:
            print(f"Comando non riconosciuto: {action}")
            update.message.reply_text("Comando non riconosciuto. Usa /start per riprovare.")
            return INIT

    def reply_to_choose_nq(self, update: Update, context: CallbackContext):
        """
        Chiede all'utente di inserire il numero di domande desiderato.
        """
        max_q = self.quiz_manager.get_number_of_questions()
        update.message.reply_text(f"Inserisci un numero di domande (massimo {max_q}):")
        return CUSTOM_NQ

    def choose_number_of_questions(self, update: Update, context: CallbackContext):
        """
        Imposta il numero di domande scelto dall'utente.
        """
        try:
            num = int(update.message.text)
            max_q = self.quiz_manager.get_number_of_questions()
            if 1 <= num <= max_q:
                self._start_quiz_for_user(update, context, num)
                return QUIZ
            else:
                update.message.reply_text(f"Numero fuori dal limite (1 - {max_q}). Riprova.")
                return CUSTOM_NQ
        except ValueError:
            update.message.reply_text("Per favore, inserisci un numero valido.")
            return CUSTOM_NQ

    def _start_quiz_for_user(self, update: Update, context: CallbackContext, n_questions: int):
        """
        Inizia il quiz per l'utente con il numero di domande specificato.
        """
        questions_ids = self.quiz_manager.pick_questions(n_questions)
        context.user_data["quiz"] = {
            "questions_ids": questions_ids,
            "current_index": 0,
            "correct_count": 0
        }
        self._send_question(update, context)

    def _send_question(self, update: Update, context: CallbackContext):
        """
        Invia la domanda corrente all'utente.
        """
        user_quiz = context.user_data["quiz"]
        idx = user_quiz["current_index"]
        q_ids = user_quiz["questions_ids"]

        if idx >= len(q_ids):
            # Quiz terminato
            return self.finish_quiz(update, context)

        q_id = q_ids[idx]
        text, options, _, _, _ = self.quiz_manager.get_question_data(q_id)

        msg = f"{text}\n\n" + "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
        update.message.reply_text(msg, reply_markup=make_keyboard_for_question(len(options)))

    def quiz_ans(self, update: Update, context: CallbackContext):
        """
        Gestisce la risposta dell'utente durante il quiz.
        """
        action = update.message.text
        if action == "Skip":
            user_quiz = context.user_data.get("quiz")
            user_quiz["current_index"] += 1
        elif action == "Cancel":
            return self.cancel_quiz(update, context)
        else:
            ans = update.message.text.upper()
            user_quiz = context.user_data.get("quiz")
            idx = user_quiz["current_index"]
            q_id = user_quiz["questions_ids"][idx]

            is_correct = self.quiz_manager.check_answer(q_id, ord(ans) - ord('A'))

            if is_correct:
                user_quiz["correct_count"] += 1
                update.message.reply_text("✅ Risposta corretta!")
            else:
                update.message.reply_text("❌ Risposta sbagliata!")
            user_quiz["current_index"] += 1

        self._send_question(update, context)


    def show_menu(self, update: Update, context: CallbackContext):
        """
        Mostra il menu principale.
        """
        update.message.reply_text(
            "Vuoi avviare un quiz? Scegli un'opzione per iniziare!",
            reply_markup=get_main_menu_keyboard()
        )
        return INIT


    def finish_quiz(self, update: Update, context: CallbackContext):
        """
        Termina il quiz, mostra il riepilogo e ritorna al menu principale.
        """
        user_quiz = context.user_data.get("quiz", {})
        correct = user_quiz.get("correct_count", 0)
        total = len(user_quiz.get("questions_ids", []))

        context.user_data["quiz"] = {}
        update.message.reply_text(
            f"🏁 Quiz terminato!\n\n"
            f"✅ Risposte corrette: {correct}/{total}\n")
        return self.show_menu(update, context)


    def cancel_quiz(self, update: Update, context: CallbackContext):
        """
        Annulla il quiz in corso.
        """
        context.user_data["quiz"] = {}
        update.message.reply_text("Quiz annullato.")
        return self.show_menu(update, context)