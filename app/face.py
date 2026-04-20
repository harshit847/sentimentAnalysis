import logging
import numpy as np
from app.config import get_settings

# Global cache for the detector
_detector = None

def get_detector():
    """Lazy load the FER detector based on settings."""
    global _detector
    if _detector is not None:
        return _detector

    # Move heavy imports inside to ensure fast startup
    try:
        from fer.fer import FER
        import cv2
    except ImportError as e:
        logging.error(f"Failed to import heavy dependencies: {e}")
        return None

    settings = get_settings()
    use_mtcnn = settings.USE_MTCNN
    
    mode_str = "MTCNN (Neural Network)" if use_mtcnn else "Haar Cascades (Fast/Light)"
    logging.info(f"Initializing FER detector in {mode_str} mode...")
    
    _detector = FER(mtcnn=use_mtcnn)
    return _detector


def analyze_face_image(img):
    try:
        if img is None:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        # Lazy load detector
        detector = get_detector()
        if detector is None:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        if len(img.shape) == 2:
            import cv2
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        if img.shape[2] != 3:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        results = detector.detect_emotions(img)

        if not results:
            return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}

        emotions = results[0]["emotions"]
        dominant_emotion = max(emotions, key=emotions.get)
        confidence = round(float(emotions[dominant_emotion]), 4)

        return {
            "emotion": dominant_emotion,
            "confidence": confidence,
            "emotions": emotions,
            "faces": len(results)
        }

    except Exception as e:
        logging.error(f"Error in analyze_face_image: {e}")
        return {"emotion": "neutral", "confidence": 1.0, "emotions": {}, "faces": 0}
