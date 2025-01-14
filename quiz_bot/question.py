class Question:
    def __init__(self, text: str, options: list, correct_index: int, verified: bool, explanation: str, topic: str):
        self.text = text
        self.options = options
        self.correct_index = correct_index
        self.verified = verified
        self.explanation = explanation
        self.topic = topic