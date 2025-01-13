# json_loader.py

import json
from typing import Dict, Any

class JSONQuestionsLoader:

    def load_from_file(self, path: str) -> Dict[int, Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            questions_list = json.load(f)

        questions_dict = {}
        for i, q in enumerate(questions_list):
            questions_dict[i] = {
                "text": q.get("text", "Domanda non disponibile"),
                "options": q.get("options", []),
                "correct_index": q.get("correct_index", 0),
                "verified": q.get("verified", False),
                "explanation": q.get("explanation", ""),
                "topic": q.get("topic", None)  # Campo opzionale per l'argomento
            }

        print(f"Loaded {len(questions_dict)} questions from {path}")

        return questions_dict