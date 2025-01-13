# quiz_manager.py

from typing import Dict, Tuple, Optional
from utils.json_loader import JSONQuestionsLoader
import random

class QuizManager:
    """
    Gestisce il database delle domande e la logica di verifica delle risposte.
    """

    def __init__(self, json_path: str):
        loader = JSONQuestionsLoader()
        self.questions_db: Dict[int, Dict] = loader.load_from_file(json_path)

    def get_number_of_questions(self) -> int:
        return len(self.questions_db)

    def pick_questions(self, n: int, exclude=None) -> list:
        if exclude is None:
            exclude = []
        available_questions = [k for k in self.questions_db.keys() if k not in exclude]
        return random.sample(available_questions, min(n, len(available_questions)))

    def check_answer(self, question_id: int, answer_index: int) -> bool:
        """Verifica se l'indice scelto corrisponde alla risposta corretta."""
        question = self.questions_db.get(question_id)
        return question and question["correct_index"] == answer_index

    def get_question_data(self, question_id: int) -> Tuple[str, list, int, str, Optional[str]]:
        """Ritorna i dettagli della domanda."""
        question = self.questions_db.get(question_id, {})
        return (
            question.get("text", "Domanda non disponibile"),
            question.get("options", []),
            question.get("correct_index", 0),
            question.get("explanation", ""),
            question.get("topic", None)
        )