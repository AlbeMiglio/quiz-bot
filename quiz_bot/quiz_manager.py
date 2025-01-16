# quiz_manager.py

from typing import Dict, Tuple, Optional, List

from quiz_bot.question import Question
from utils.json_loader import JSONQuestionsLoader
import random

class QuizManager:
    """
    Gestisce il database delle domande e la logica di verifica delle risposte.
    """

    def __init__(self, json_path: str):
        loader = JSONQuestionsLoader()
        self.questions_db: Dict[int, Question] = loader.load_from_file(json_path)
        self.cached_topics: List[str] = []  # Siccome la lista di topics cambia raramente e solo nel caso 
                                            # venga aggiunta una domanda, salvo la lista in cache per efficienza
        self._cache_topics()  # metodo per salvare in cache la lista di topic. 

    def get_number_of_questions(self, topic=None) -> int:
        if topic is None: 
            return len(self.questions_db)
        else: 
            return sum(1 for question in self.questions_db.values() if question.topic.lower() == topic.lower())


    def pick_questions(self, n: int, exclude=None) -> list:
        if exclude is None:
            exclude = []
        available_questions = [k for k in self.questions_db.keys() if k not in exclude]
        return random.sample(available_questions, min(n, len(available_questions)))

    def check_answer(self, question_id: int, answer_index: int, scramble_map: dict) -> bool:
        """Verifica se l'indice scelto corrisponde alla risposta corretta."""
        question = self.questions_db.get(question_id)
        ans = answer_index
        if scramble_map:
            ans = scramble_map.get(answer_index)
        return question and question.correct_index == ans

    def get_question_data(self, question_id: int) -> Question:
        """Ritorna i dettagli della domanda."""
        return self.questions_db.get(question_id)
    
    def extract_list_of_all_topics(self) -> list:
        """Estrae tutti gli argomenti per cui ci sono domande nel database"""
        return self.cached_topics
    
    def _cache_topics(self):
        """Salva in cache la lista di topic disponibili"""
        self.cached_topics = list({question.topic for question in self.questions_db.values()})

    def exclude_questions_not_related_to_selected_topic(self, topic: str) -> list:
        """  Ritorna gli indici di tutte le domande che non appartengono all'argomento selezionato.
        """
        return [k for k, question in self.questions_db.items() if question.topic.lower() != topic.lower()]
    