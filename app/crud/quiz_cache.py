import json
import logging
from redis.exceptions import RedisError
from app.utils.redis_client import redis_client
from app.schemas.quiz import QuizQuestion

logger = logging.getLogger(__name__)
QUIZ_TTL = 3600  # 60 mins

def store_quiz(quiz_id: str, user_id: int, questions: list):
    try:
        redis_client.setex(
            f"quiz:{quiz_id}",
            QUIZ_TTL,
            json.dumps({
                "user_id": user_id,
                "questions": questions
            })
        )
        return True
    
    except RedisError:
        logger.exception("Failed to cache quiz %s in Redis", quiz_id)
        return False

def get_quiz(quiz_id: str, user_id: int):
    try:
        raw_data = redis_client.get(f"quiz:{quiz_id}")

        if not raw_data:
            logger.warning("Quiz %s not found or expired", quiz_id)
            return None

        data = json.loads(raw_data)

        if data["user_id"] != user_id:
            logger.warning(
                "User %s tried to submit quiz %s which they have not created", user_id, quiz_id
            )
            return None

        return [QuizQuestion(**q) for q in data["questions"]]

    except RedisError:
        logger.exception("Failed to fetch quiz %s from Redis", quiz_id)
        return None