# json_loader.py

import json
from typing import Dict, Any

from quiz_bot.question import Question


class JSONQuestionsLoader:

    def load_from_file(self, path: str) -> Dict[int, Question]:
        with open(path, "r", encoding="utf-8") as f:
            questions_list = json.load(f)

        questions_dict = {}
        for i, q in enumerate(questions_list):
            text = q.get("text", "Domanda non disponibile")
            options = q.get("options", [])
            correct_index = q.get("correct_index", 0)
            verified = q.get("verified", False)
            explanation = q.get("explanation", "")
            topic = q.get("topic", None)
            q = Question(text, options, correct_index, verified, explanation, topic)
            questions_dict[i] = q

        print(f"Loaded {len(questions_dict)} questions from {path}")

        return questions_dict