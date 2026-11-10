import json
import os
from typing import Dict, List, Any
from app.config import QUESTIONS_PATH

_cached_questions: Dict[str, Any] = {}

def load_questions() -> Dict[str, Any]:
    global _cached_questions
    if not _cached_questions:
        if not os.path.exists(QUESTIONS_PATH):
            raise FileNotFoundError(f"Questions file not found: {QUESTIONS_PATH}")
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            _cached_questions = json.load(f)
    return _cached_questions

def get_directions() -> List[Dict[str, str]]:
    data = load_questions()
    directions = []
    for key, val in data.items():
        directions.append({
            "id": key,
            "title": val.get("title", key)
        })
    return directions

def get_questions_for_direction(direction_id: str) -> List[Dict[str, Any]]:
    data = load_questions()
    if direction_id in data:
        return data[direction_id].get("questions", [])
    return []

def get_direction_title(direction_id: str) -> str:
    data = load_questions()
    if direction_id in data:
        return data[direction_id].get("title", direction_id)
    return direction_id
