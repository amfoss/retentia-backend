from typing import List
from sqlalchemy.orm import Session as DBSession
from app.schemas.quiz import QuizQuestion, UserResponse, EvaluatedQuestion, ConceptRetention
from app.models import Retention, Concept, Chapter, Topic, Subject
from sqlalchemy import select
from app.retentia_algorithm import new_concept_retention, existing_concept_retention

def evaluate(picked: int, options: List[str], correct: str):
    if picked == -1:
        return "skipped"
    if picked < 0 or picked >= len(options):
        return "wrong"
    return "correct" if options[picked] == correct else "wrong"

def evaluate_quiz(db: DBSession, user_id: int, quiz_data: List[QuizQuestion], user_responses: List[UserResponse]):
    evaluation = []
    concept_retention = []
    concept_data = {}

    for i in range(len(quiz_data)):
        if user_responses[i].question_id != i or quiz_data[i].question_id != i:
            raise RuntimeError("No content integrity")

        result = evaluate(
            picked=user_responses[i].submitted_answer,
            options=quiz_data[i].options,
            correct=quiz_data[i].correct_answer,
        )
        related_concepts = quiz_data[i].related_concepts

        evaluation.append(
            EvaluatedQuestion(
                question=quiz_data[i].question,
                options=quiz_data[i].options,
                correct_answer=quiz_data[i].correct_answer,
                submitted_answer=user_responses[i].submitted_answer,
                result=result,
                related_concepts=related_concepts
            )
        )

        for concept in related_concepts:
            if concept not in concept_data:
                concept_data[concept] = []
            concept_data[concept].append(result)

    for concept in concept_data:
        row = db.execute(
            select(Concept, Chapter, Topic, Subject)
            .join(Chapter, Concept.chapter_id == Chapter.id)
            .join(Topic, Chapter.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .where(Concept.name == concept)
        ).first()

        if row is None:
            continue

        concept_obj, chapter_obj, topic_obj, subject_obj = row

        existing_row = db.execute(
            select(Retention)
            .where(Retention.user_id == user_id)
            .where(Retention.concept_id == concept_obj.id)
        ).scalar_one_or_none()

        if existing_row is None:
            retention, next_revision_date = new_concept_retention(
                correct=concept_data[concept].count("correct"),
                wrong=concept_data[concept].count("wrong"),
                skipped=concept_data[concept].count("skipped"),
                threshold=0.70
            )
            db.add(
                Retention(
                    user_id=user_id,
                    concept_id=concept_obj.id,
                    retention=retention,
                    next_revision_date=next_revision_date,
                )
            )
        else:
            retention, next_revision_date = existing_concept_retention(
                correct=concept_data[concept].count("correct"),
                wrong=concept_data[concept].count("wrong"),
                skipped=concept_data[concept].count("skipped"),
                old_retention=existing_row.retention,
                threshold=0.70
            )
            existing_row.retention = retention
            existing_row.next_revision_date = next_revision_date

        concept_retention.append(
            ConceptRetention(
                concept=concept_obj.name,
                retention=retention,
                topic=topic_obj.name,
                chapter=chapter_obj.name,
                subject=subject_obj.name,
                next_review_date=next_revision_date,
            )
        )

    db.commit()

    return evaluation, concept_retention


def get_retention_data(db: DBSession, user_id: int, concept_ids: list[str]):
    rows = db.execute(
        select(Retention)
        .where(Retention.user_id == user_id)
        .where(Retention.concept_id.in_(concept_ids))
    ).scalars().all()

    retention = {row.concept_id: row.retention for row in rows}

    for concept_id in concept_ids:
        if concept_id not in retention:
            retention[concept_id] = -1

    return retention


def save_retention_data(db: DBSession,user_id: int,concept_data: dict[int, ConceptRetention]):
    for concept_id, retention in concept_data.items():
        row = db.execute(
            select(Retention)
            .where(Retention.user_id == user_id)
            .where(Retention.concept_id == concept_id)
        ).scalar_one_or_none()

        if row is None:
            db.add(Retention(
                user_id=user_id,
                concept_id=concept_id,
                retention=retention.retention,
                next_revision_date=retention.next_review_date
            ))
        else:
            row.retention = retention.retention
            row.next_revision_date = retention.next_review_date

    db.commit()