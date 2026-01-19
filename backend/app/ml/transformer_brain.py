import torch
from transformers import pipeline
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Brain")

print("🤖 Loading DeBERTa v3 Brain...")

# 🚀 AUTO-DETECT GPU
device = 0 if torch.cuda.is_available() else -1
device_name = torch.cuda.get_device_name(0) if device == 0 else "CPU"

print(f"   ⚙️ Hardware Acceleration: {device_name} 🟢")

# The Smart Model
model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"

try:
    classifier = pipeline(
        "zero-shot-classification", 
        model=model_name,
        device=device 
    )
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise e

def predict_difficulty_with_transformer(text):
    """
    Returns: { "difficulty": "Novice" | "Apprentice" | "Contributor", "score": 0.95 }
    """
    candidate_labels = [
        "easy documentation fix or typo correction",         # Novice
        "standard feature implementation or bug fix",        # Apprentice
        "complex architectural change or core performance"   # Contributor
    ]
    
    # Safety Check: Empty Text
    if not text or len(text.strip()) == 0:
        return {"difficulty": "Reject", "score": 0.0}

    try:
        # Run Inference (Limit to 1024 chars for speed & memory safety)
        result = classifier(text[:1024], candidate_labels, multi_label=False)
        
        top_label = result['labels'][0]
        score = result['scores'][0]
        
        difficulty = "Apprentice"
        if top_label == "easy documentation fix or typo correction":
            difficulty = "Novice"
        elif top_label == "complex architectural change or core performance":
            difficulty = "Contributor"
        
        return {
            "difficulty": difficulty,
            "score": float(score)
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return {"difficulty": "Reject", "score": 0.0}