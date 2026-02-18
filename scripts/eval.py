import json
import os
from app.scoring.baseline import baseline_select_skills
from app.config import settings

file_dir = os.path.dirname(__file__)
eval_f = json.load(open(os.path.join(file_dir, "../data", "eval_cases_real.json"), "r"))

CATEGORIES = ["technology", "programming", "concepts"]

def eval_case(selected_skills: dict, expected: dict) -> dict:
    """
    Compare selected_skills against expected (trimmed to top_n per category).

    Score per category: Jaccard index = |hits| / (|hits| + |missing| + |unexpected|)
    This penalises both missing expected items and unexpected extras equally.

    Returns:
        scores:        per-category Jaccard score (0-1)
        average_score: mean of the three category scores
        mistakes:      per-category lists of missing and unexpected items
    """
    top_n = settings.TOP_N
    scores = {}
    mistakes = {}

    for cat in CATEGORIES:
        selected_set = set(selected_skills.get(cat, []))
        expected_set = set(expected.get(cat, [])[:top_n])

        hits = selected_set & expected_set
        missing = sorted(expected_set - selected_set)
        unexpected = sorted(selected_set - expected_set)

        denominator = len(hits) + len(missing) + len(unexpected)
        scores[cat] = round(len(hits) / denominator, 4) if denominator > 0 else 1.0

        mistakes[cat] = {"missing": missing, "unexpected": unexpected}

    average_score = round(sum(scores.values()) / len(CATEGORIES), 4)

    return {
        "scores": scores,
        "average_score": average_score,
        "mistakes": mistakes,
    }

def evaluate():
    results = []
    score_sum = 0.0
    for case in eval_f:
        job_role = case["input"]["job_role"]
        technology = case["input"]["technology"]
        programming = case["input"]["programming"]
        concepts = case["input"]["concepts"]
        
        expected = case["expected"]

        selected_skills, details = baseline_select_skills(
            job_role=job_role,
            technology=technology,
            programming=programming,
            concepts=concepts,
            # job_text=,
            # top_n=,
            dev_mode=True,
            include_zero=False
        )

        evaluation = eval_case(selected_skills, expected)

        results.append({
            "job_role": job_role,
            "evaluation": evaluation
        })

        score_sum += evaluation["average_score"]
    
    average_score = round(score_sum / len(results), 4)
    return {
        "results": results,
        "overall_score": average_score,
        "top_n": settings.TOP_N
    }

if __name__ == "__main__":
    eval_results = evaluate()
    print(json.dumps(eval_results, indent=2))
