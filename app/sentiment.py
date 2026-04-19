from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List


class VaderSentimentService:
    def __init__(self) -> None:
        self._analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> Dict:
        scores = self._analyzer.polarity_scores(text)
        compound = scores.get("compound", 0.0)
        label = (
            "positive" if compound >= 0.05
            else "negative" if compound <= -0.05
            else "neutral"
        )
        confidence = abs(compound)
        return {
            "label": label,
            "confidence": confidence,
            "scores": scores,
        }

    def analyze_texts(self, texts: List[str]) -> List[Dict]:
        return [self.analyze(text) for text in texts]


if __name__ == "__main__":
    service = VaderSentimentService()

    sample_text = "I really love this product, it's amazing!"
    result = service.analyze(sample_text)
    print("Single Text Analysis:")
    print(result)

    texts = [
        "I am very happy today!",
        "This is the worst day ever.",
        "It's okay, nothing special."
    ]
    results = service.analyze_texts(texts)
    print("\nMultiple Texts Analysis:")
    for t, r in zip(texts, results):
        print(f"Text: {t}\nResult: {r}\n")
