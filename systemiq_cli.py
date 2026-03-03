from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


KNOWLEDGE_PATH = Path(__file__).parent / "knowledge" / "knowledge_base.json"


def load_knowledge_base(path: Path = KNOWLEDGE_PATH) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
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


def should_ask_question(facts: dict[str, str | None], fact: str, smart_mode: bool) -> bool:
    if not smart_mode:
        return True
    
    if facts.get("power_led") == "no":
        if fact in ["fan_speed", "beep_code", "bios_access", "ram_status", "hdd_status",
                    "boot_device_found", "os_loads", "blue_screen", "artifacts",
                    "display_output", "overheating", "high_noise", "usb_devices_fail",
                    "network_link"]:
            return False
    
    if facts.get("bios_access") == "no":
        if fact in ["ram_status", "hdd_status", "boot_device_found"]:
            return False
    
    if facts.get("hdd_status") == "no":
        if fact in ["boot_device_found", "os_loads"]:
            return False
    
    if facts.get("display_output") == "no":
        if fact == "artifacts":
            return False
    
    if facts.get("os_loads") == "no":
        if fact == "blue_screen":
            return False
    
    if facts.get("fan_speed") == "stopped":
        if fact == "high_noise":
            return False
    
    if fact == "display_output":
        if facts.get("bios_access") is None and facts.get("power_led") == "yes":
            return True
    
    if fact == "boot_device_found":
        if facts.get("bios_access") == "no" or facts.get("hdd_status") == "no":
            return False
    
    if fact == "network_link":
        if facts.get("os_loads") == "no":
            return False
    
    if fact == "usb_devices_fail":
        if facts.get("bios_access") == "no" and facts.get("os_loads") == "no":
            return False
    
    return True


def ask_question(facts: dict[str, str | None], fact: str) -> None:
    question = FACT_DEFINITIONS[fact]["question"]
    valid_answers = FACT_DEFINITIONS[fact]["answers"]

    while True:
        answer = input(question).strip().lower()
        if answer in valid_answers:
            facts[fact] = answer
            return
        print(f"Invalid input. Please provide one of: {', '.join(sorted(valid_answers))}.")


def evaluate_rules(facts: dict[str, str | None]) -> list[dict[str, object]]:
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


def unresolved_relevant_facts(facts: dict[str, str | None], smart_mode: bool = True) -> list[str]:
    unknown_counts: Counter[str] = Counter()

    for rule in RULES:
        contradicted = any(
            facts.get(fact) is not None and facts.get(fact) != expected
            for fact, expected in rule["conditions"].items()
        )
        if contradicted:
            continue

        for fact in rule["conditions"]:
            if facts[fact] is None and should_ask_question(facts, fact, smart_mode):
                unknown_counts[fact] += 1

    if not unknown_counts:
        return []

    return [fact for fact, _ in unknown_counts.most_common()]


def interactive_session(mode: str = "smart") -> None:
    smart_mode = mode.lower() == "smart"
    facts = FACTS_TEMPLATE.copy()

    print("Welcome to SystemIQ — Intelligent PC Hardware Troubleshooter!")
    if smart_mode:
        print("Running in SMART mode: Questions adapt based on your answers.")
    else:
        print("Running in ALL mode: All questions will be asked for comprehensive analysis.")
    print("Answer the questions to receive ranked diagnoses with explanations.\n")

    while True:
        queue = unresolved_relevant_facts(facts, smart_mode)
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
    mode = "smart"
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--all", "-a", "all"]:
            mode = "all"
        elif arg in ["--smart", "-s", "smart"]:
            mode = "smart"
        elif arg in ["--help", "-h", "help"]:
            print("SystemIQ — Intelligent PC Hardware Troubleshooter")
            print("\nUsage:")
            print("  python systemiq_cli.py [mode]")
            print("\nModes:")
            print("  smart, -s, --smart    Smart mode (default): Skips irrelevant questions")
            print("  all, -a, --all        All mode: Asks all questions for comprehensive data")
            print("\nExamples:")
            print("  python systemiq_cli.py              # Run in smart mode")
            print("  python systemiq_cli.py smart        # Run in smart mode")
            print("  python systemiq_cli.py all          # Run in all mode")
            sys.exit(0)
        else:
            print(f"Unknown mode: {sys.argv[1]}")
            print("Use --help for usage information.")
            sys.exit(1)
    
    interactive_session(mode)
