from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class Chapter(BaseModel):
    chapter: str
    concepts: List[str]
    
class Subject(BaseModel):
    subject: str
    chapters: List[Chapter]
    
class QuizQuestion(BaseModel):
    question_id: int
    chapter: str
    question: str
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    related_concepts: List[str]
        
class QuizQuestionSafe(BaseModel):
    question_id: int
    question: str
    options: List[str] = Field(min_length=4, max_length=4)
 
class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestionSafe]
        
QUIZ_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "chapter": {"type": "string"},
            "question": {"type": "string"},
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 4,
                "maxItems": 4
            },
            "correct_answer": {"type": "string"},
            "related_concepts": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": [
            "chapter",
            "question",
            "options",
            "correct_answer",
            "related_concepts"
        ]
    }
}

class UserResponse(BaseModel):
    question_id: int
    submitted_answer: int

class SubmitQuiz(BaseModel):
    quiz_id: str
    user_responses: List[UserResponse]

class ConceptRetention(BaseModel):
    concept: str
    retention: int
    topic: str
    chapter: str
    subject: str
    next_review_date: datetime

class EvaluatedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    submitted_answer: int
    result: str
    related_concepts: List[str]

class SubmitQuizResponse(BaseModel):
    quiz_id: str
    evaluation: List[EvaluatedQuestion]
    concept_retention: List[ConceptRetention] 
