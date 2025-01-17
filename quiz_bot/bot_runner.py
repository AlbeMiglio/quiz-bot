import datetime
import random

from telegram import Update
from telegram.ext import Updater, CallbackContext, PicklePersistence, CommandHandler, ConversationHandler

from .quiz_manager import QuizManager
from .handlers import build_main_conversation, get_main_menu_keyboard, make_keyboard_for_question, make_keyboard_for_topics, BUTTONS, INIT, CUSTOM_NQ, QUIZ, TOPIC

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
        elif action == "select_topic":
            self.reply_to_choose_topic(update, context)
            return TOPIC
        else:
            print(f"Comando non riconosciuto: {action}")
            update.message.reply_text("Comando non riconosciuto. Usa /start per riprovare.")
            return INIT

    def reply_to_choose_nq(self, update: Update, context: CallbackContext):
        """
        Chiede all'utente di inserire il numero di domande desiderato.
        """
        selected_topic = context.user_data.get("selected_topic")
        if selected_topic:
            max_q = self.quiz_manager.get_number_of_questions(selected_topic)
            text_topic = f"per l'argomento {selected_topic}"
        else:
            max_q = self.quiz_manager.get_number_of_questions()
            text_topic = ""

        update.message.reply_text(f"Inserisci un numero di domande {text_topic} (massimo {max_q}):")
        return CUSTOM_NQ

    def choose_number_of_questions(self, update: Update, context: CallbackContext):
        """
        Imposta il numero di domande scelto dall'utente.
        """
        try:
            num = int(update.message.text)
            selected_topic = context.user_data.get("selected_topic")
            if selected_topic:
                max_q = self.quiz_manager.get_number_of_questions(selected_topic)
            else:
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
        
    def reply_to_choose_topic(self, update: Update, context: CallbackContext):
        """
        Chiede all'utente di scegliere l'argomento.
        """
        list_topics = self.quiz_manager.extract_list_of_all_topics()
        update.message.reply_text("Seleziona l'argomento su cui ti vuoi allenare:", reply_markup=make_keyboard_for_topics(list_topics))
        return TOPIC
    
    def choose_topic(self, update: Update, context: CallbackContext):
        """
        Imposta l'argomento scelto dall'utente
        """
        try:
            selected_topic = update.message.text
            list_topics = self.quiz_manager.extract_list_of_all_topics()
            if selected_topic in list_topics:
                context.user_data["selected_topic"] = selected_topic
                current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                print(f"[{current_time}] User {update.effective_user.username} selected topic: {selected_topic}")
                self.reply_to_choose_nq(update, context)
                return CUSTOM_NQ
            else:
                update.message.reply_text("L'argomento scelto non è valido. Selezionare un argomento tra quelli proposti")
                return TOPIC
        except ValueError:
            update.message.reply_text("Per favore, seleziona un argomento tra quelli proposti.")
            return TOPIC

    def _start_quiz_for_user(self, update: Update, context: CallbackContext, n_questions: int):
        """
        Inizia il quiz per l'utente con il numero di domande e l'argomento specificato.
        """
        selected_topic = context.user_data.get("selected_topic")
        if selected_topic:
            excluded_keys = self.quiz_manager.exclude_questions_not_related_to_selected_topic(selected_topic)
        else:
            excluded_keys = None
        questions_ids = self.quiz_manager.pick_questions(n_questions, excluded_keys)

        context.user_data["quiz"] = {
            "questions_ids": questions_ids,
            "current_question_scramble_map": {},
            "current_index": 0,
            "correct_count": 0,
            "wrong_count" : 0
        }
        current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"[{current_time}] User {update.effective_user.username} started a quiz with {n_questions} questions.")
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
            self.finish_quiz(update, context)
            return INIT

        q_id = q_ids[idx]
        q = self.quiz_manager.get_question_data(q_id)
        text = q.text
        scrambled_options_map = user_quiz["current_question_scramble_map"]
        if not scrambled_options_map:
            scrambled_options_map = {}
        scrambled_options_map.clear()
        answers_set = [i for i in range(len(q.options))]
        cnt = 0
        while cnt < len(q.options):
            i = random.randint(0, len(answers_set)-1)
            val = answers_set.pop(i)
            scrambled_options_map[cnt] = val
            cnt += 1
        user_quiz["current_question_scramble_map"] = scrambled_options_map
        options = [q.options[scrambled_options_map[i]] for i in range(len(q.options))]
        text = f"Domanda {idx + 1}/{len(q_ids)}:\n{text}"
        msg = f"{text}\n\n" + "\n\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
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

            chosen_option = ord(ans) - ord('A')
            q = self.quiz_manager.get_question_data(q_id)
            if chosen_option < 0 or chosen_option >= len(q.options):
                update.message.reply_text("Opzione non valida. Riprova!", reply_markup=make_keyboard_for_question(len(q.options)))
                return QUIZ
            is_correct = self.quiz_manager.check_answer(q_id, chosen_option, user_quiz["current_question_scramble_map"])

            if is_correct:
                user_quiz["correct_count"] += 1
                text = "✅ Risposta corretta!"
            else:
                user_quiz["wrong_count"] += 1
                text = "❌ Risposta sbagliata!"
                correct = user_quiz["current_question_scramble_map"][q.correct_index]
                text += f"\n\nRisposta corretta: ||{chr(correct + ord('A'))}||"

            verified = q.verified
            expl = q.explanation if verified else "Spiegazione non disponibile."
            text += f"\n\nCommento: {expl}"
            text = self._escape_markdown(text)
            update.message.reply_text(text, parse_mode="MarkdownV2")

            current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            print(f"[{current_time}] User {update.effective_user.username} answered {ans} for question {q_id}. Correct: {is_correct}")
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
    
    def _calculate_score(self, numOfCorrect, numOfWrong):
        score = numOfWrong*(-0.33) + numOfCorrect*(1)
        return score


    def finish_quiz(self, update: Update, context: CallbackContext):
        """
        Termina il quiz, mostra il riepilogo e ritorna al menu principale.
        """
        user_quiz = context.user_data.get("quiz", {})
        correct = user_quiz.get("correct_count", 0)
        wrong = user_quiz.get("wrong_count", 0)
        total = len(user_quiz.get("questions_ids", []))

        score = self._calculate_score(numOfCorrect=correct, numOfWrong=wrong)

        context.user_data["quiz"] = {}
        context.user_data["selected_topic"] = None
        current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"[{current_time}] User {update.effective_user.username} finished the quiz. Correct: {correct}/{total}")
        update.message.reply_text(
            f"🏁 Quiz terminato!\n\n"
            f"✅ Risposte corrette: {correct}/{total}\n\n"
            f"👉 Punteggio finale ottenuto: {score:.2f}")
        self.show_menu(update, context)
        return INIT


    def cancel_quiz(self, update: Update, context: CallbackContext):
        """
        Annulla il quiz in corso.
        """
        context.user_data["quiz"] = {}
        context.user_data["selected_topic"] = None
        print(f"User {update.effective_user.username} cancelled the quiz.")
        update.message.reply_text("Quiz annullato.")
        return self.show_menu(update, context)

    def _escape_markdown(self, text: str) -> str:
        escape_chars = r'\_*[]()~`>#+-={}.!'
        return ''.join(f'\\{char}' if char in escape_chars else char for char in text)