from __future__ import annotations

import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from collections import Counter

from systemiq_cli import load_knowledge_base, KNOWLEDGE_PATH

app = Flask(__name__)

FACT_DEFINITIONS, RULES = load_knowledge_base(KNOWLEDGE_PATH)


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_session():
    data = request.json
    mode = data.get('mode', 'smart')
    smart_mode = mode.lower() == 'smart'
    
    facts = {fact: None for fact in FACT_DEFINITIONS}
    next_facts = unresolved_relevant_facts(facts, smart_mode)
    
    if next_facts:
        next_fact = next_facts[0]
        return jsonify({
            'status': 'continue',
            'next_question': {
                'fact': next_fact,
                'question': FACT_DEFINITIONS[next_fact]['question'],
                'answers': sorted(list(FACT_DEFINITIONS[next_fact]['answers']))
            },
            'facts': facts,
            'mode': mode
        })
    
    return jsonify({'status': 'error', 'message': 'No questions available'})


@app.route('/api/answer', methods=['POST'])
def submit_answer():
    data = request.json
    facts = data.get('facts', {})
    fact = data.get('fact')
    answer = data.get('answer', '').strip().lower()
    mode = data.get('mode', 'smart')
    smart_mode = mode.lower() == 'smart'
    
    if fact not in FACT_DEFINITIONS:
        return jsonify({'status': 'error', 'message': 'Invalid fact'}), 400
    
    if answer not in FACT_DEFINITIONS[fact]['answers']:
        return jsonify({
            'status': 'invalid_answer',
            'message': f"Invalid input. Please provide one of: {', '.join(sorted(FACT_DEFINITIONS[fact]['answers']))}"
        }), 400
    
    facts[fact] = answer
    
    next_facts = unresolved_relevant_facts(facts, smart_mode)
    
    if next_facts:
        next_fact = next_facts[0]
        return jsonify({
            'status': 'continue',
            'next_question': {
                'fact': next_fact,
                'question': FACT_DEFINITIONS[next_fact]['question'],
                'answers': sorted(list(FACT_DEFINITIONS[next_fact]['answers']))
            },
            'facts': facts
        })
    
    diagnoses = evaluate_rules(facts)
    
    if not diagnoses:
        return jsonify({
            'status': 'complete',
            'diagnoses': [],
            'message': 'No confident diagnosis could be produced from current answers.'
        })
    
    return jsonify({
        'status': 'complete',
        'diagnoses': diagnoses,
        'facts': facts
    })


@app.route('/api/facts', methods=['GET'])
def get_facts():
    facts_info = {}
    for fact, definition in FACT_DEFINITIONS.items():
        facts_info[fact] = {
            'question': definition['question'],
            'answers': sorted(list(definition['answers']))
        }
    return jsonify(facts_info)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
