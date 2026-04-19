from fer.fer import FER
import cv2
import numpy as np

detector = FER(mtcnn=True)

def analyze_face_image(img):
    try:
        if img is None:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        if img.shape[2] != 3:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

 
        results = detector.detect_emotions(img)

        if not results:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        emotions = results[0]["emotions"]
        dominant_emotion = max(emotions, key=emotions.get)  # pick highest score
        confidence = round(float(emotions[dominant_emotion]), 4)

        return {
            "emotion": dominant_emotion,
            "confidence": confidence,
            "emotions": emotions,
            "faces": len(results)
        }

    except Exception as e:
        return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}
