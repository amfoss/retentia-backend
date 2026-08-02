from datetime import datetime, timedelta


def days_from_retention(retention: int):
    if retention < 40:
        return 1
    elif retention < 60:
        return 2
    elif retention < 75:
        return 4
    elif retention < 85:
        return 7
    elif retention < 95:
        return 14
    else:
        return 30

def next_revision_date(retention: int) -> datetime:
    days = days_from_retention(retention)
    return datetime.utcnow() + timedelta(days=days)


def session_score(correct: int, wrong: int, skipped: int):
    total = correct + wrong + skipped
    if total == 0:
        return 0.0, 0.0, 0.0

    attempted = correct + wrong
    accuracy = correct / attempted if attempted else 0.0
    completion = attempted / total

    score = accuracy * completion
    return score, accuracy, completion

def new_concept_retention(
    correct: int, wrong: int, skipped: int, threshold: float = 0.70):
    score, _, _ = session_score(correct, wrong, skipped)
    retention = round(max(0.0, min(1.0, score)) * 100)
    return retention, next_revision_date(retention)

def existing_concept_retention(
    correct: int,
    wrong: int,
    skipped: int,
    old_retention: int | None,
    threshold: float = 0.70,
):
    if old_retention is None:
        return new_concept_retention(correct, wrong, skipped, threshold)

    score, accuracy, _ = session_score(correct, wrong, skipped)
    attempted = correct + wrong

    if attempted == 0:
        return old_retention, next_revision_date(old_retention)

    old_frac = old_retention / 100
    alpha = min(0.6, 0.15 + 0.05 * attempted)
    new_frac = (1 - alpha) * old_frac + alpha * score

    if accuracy >= threshold:
        new_frac = min(1.0, new_frac + 0.02)
    elif accuracy < threshold * 0.5:
        new_frac = max(0.0, new_frac - 0.02)

    retention = round(max(0.0, min(1.0, new_frac)) * 100)
    return retention, next_revision_date(retention)