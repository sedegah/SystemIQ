"""SystemIQ — Intelligent PC Hardware Troubleshooter CLI.

A rule-based expert system that asks adaptive troubleshooting questions,
then ranks likely diagnoses with confidence factors and explanations.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


KNOWLEDGE_PATH = Path(__file__).parent / "knowledge" / "knowledge_base.json"


def load_knowledge_base(path: Path = KNOWLEDGE_PATH) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    """Load and normalize fact definitions and rules from the JSON knowledge base."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    facts = data.get("facts", {})
    rules = data.get("rules", [])

    normalized_facts: dict[str, dict[str, object]] = {}
    for fact, definition in facts.items():
        answers = definition.get("answers", [])
        normalized_facts[fact] = {
            "question": definition.get("question", f"Provide value for {fact}: "),
            "answers": set(answers),
        }

    return normalized_facts, rules


FACT_DEFINITIONS, RULES = load_knowledge_base()
FACTS_TEMPLATE = {fact: None for fact in FACT_DEFINITIONS}


def ask_question(facts: dict[str, str | None], fact: str) -> None:
    """Prompt until a valid answer is provided for a specific fact."""
    question = FACT_DEFINITIONS[fact]["question"]
    valid_answers = FACT_DEFINITIONS[fact]["answers"]

    while True:
        answer = input(question).strip().lower()
        if answer in valid_answers:
            facts[fact] = answer
            return
        print(f"Invalid input. Please provide one of: {', '.join(sorted(valid_answers))}.")


def evaluate_rules(facts: dict[str, str | None]) -> list[dict[str, object]]:
    """Return matching diagnoses sorted by descending confidence factor."""
    matches = []
    for rule in RULES:
        if all(facts.get(fact) == value for fact, value in rule["conditions"].items()):
            matches.append(
                {
                    "rule_id": rule["id"],
                    "diagnosis": rule["diagnosis"],
                    "cf": rule["cf"],
                    "explanation": rule["explanation"],
                }
            )
    return sorted(matches, key=lambda item: item["cf"], reverse=True)


def unresolved_relevant_facts(facts: dict[str, str | None]) -> list[str]:
    """Return unknown facts still relevant to potentially satisfiable rules."""
    unknown_counts: Counter[str] = Counter()

    for rule in RULES:
        contradicted = any(
            facts.get(fact) is not None and facts.get(fact) != expected
            for fact, expected in rule["conditions"].items()
        )
        if contradicted:
            continue

        for fact in rule["conditions"]:
            if facts[fact] is None:
                unknown_counts[fact] += 1

    if not unknown_counts:
        return []

    return [fact for fact, _ in unknown_counts.most_common()]


def interactive_session() -> None:
    """Run the complete adaptive troubleshooting dialog."""
    facts = FACTS_TEMPLATE.copy()

    print("Welcome to SystemIQ — Intelligent PC Hardware Troubleshooter!")
    print("Answer the questions to receive ranked diagnoses with explanations.\n")

    while True:
        queue = unresolved_relevant_facts(facts)
        if not queue:
            break
        ask_question(facts, queue[0])

    diagnoses = evaluate_rules(facts)

    print("\nEvaluating knowledge base...\n")
    if not diagnoses:
        print("No confident diagnosis could be produced from current answers.")
        print("Try running again and providing more precise symptom details.")
        return

    print("Diagnosis ranking:")
    for result in diagnoses:
        print(f"- {result['diagnosis']}: CF={result['cf']:.2f} (via {result['rule_id']})")

    print("\nExplanations:")
    for result in diagnoses:
        print(f"- {result['rule_id']}: {result['explanation']}")


if __name__ == "__main__":
    interactive_session()
