# SystemIQ — Intelligent PC Hardware Troubleshooter

SystemIQ is an interactive, explainable expert system for diagnosing PC hardware and boot issues using a **knowledge base of facts, rules, and confidence factors**. The system uses intelligent question adaptation to minimize unnecessary questions and provide accurate diagnostics efficiently.

## Features

### Smart Question Adaptation
SystemIQ features two diagnostic modes:

- **Smart Mode (Default)**: Intelligently skips irrelevant questions based on previous answers
  - If power LED is off, skips questions about BIOS, OS, and other components
  - If BIOS is inaccessible, skips questions about BIOS-visible hardware status
  - If no display output, skips questions about visual artifacts
  - If OS doesn't load, skips runtime-specific questions
  - And more conditional logic to streamline diagnostics

- **All Mode**: Asks all questions for comprehensive data collection
  - Useful for thorough documentation or edge cases
  - Provides complete dataset for knowledge base refinement

### Confidence-Based Ranking
- Diagnoses are ranked by confidence factor (CF)
- Each diagnosis includes the triggering rule ID and explanation
- Multiple diagnoses may be returned when symptoms overlap

### JSON-Driven Knowledge Base
- Easily extensible without modifying Python code
- Facts define diagnostic questions and valid answers
- Rules define condition-diagnosis mappings with confidence factors
- Clean separation between logic and domain knowledge

## Installation

No dependencies required! SystemIQ uses only Python standard library.

```bash
# Clone or download the repository
cd SystemIQ
```

## Usage

### Quick Start

Run SystemIQ in smart mode (default):
```bash
python systemiq_cli.py
```

### Command-Line Options

```bash
# Smart mode (adaptive questions)
python systemiq_cli.py smart
python systemiq_cli.py --smart
python systemiq_cli.py -s

# All mode (ask all questions)
python systemiq_cli.py all
python systemiq_cli.py --all
python systemiq_cli.py -a

# Help
python systemiq_cli.py --help
python systemiq_cli.py -h
```

### Example Session (Smart Mode)

```
$ python systemiq_cli.py

Welcome to SystemIQ — Intelligent PC Hardware Troubleshooter!
Running in SMART mode: Questions adapt based on your answers.
Answer the questions to receive ranked diagnoses with explanations.

Can you enter BIOS/UEFI setup? (yes/no): no
Is the power LED on? (yes/no): yes
Do you hear BIOS beep codes? (none/short/long/repeated): short
Are system fans spinning? (normal/slow/stopped): normal
Does the PC overheat or shut down under load? (yes/no): yes
Do you see visual artifacts/flickering on display? (yes/no): yes
Are fan noises unusually loud at idle? (yes/no): yes

Evaluating knowledge base...

Diagnosis ranking:
- gpu_overheating_or_vram_fault: CF=0.89 (via R10)
- motherboard_failure: CF=0.85 (via R4)
- dust_buildup_or_bearing_wear: CF=0.72 (via R18)

Explanations:
- R10: Visual artifacts combined with heat often indicate GPU thermal or VRAM issues.
- R4: Short POST beeps with no BIOS access suggest motherboard fault.
- R18: Normal RPM but loud fan noise usually indicates dust buildup or worn bearings.
```

Notice how in the example above, smart mode automatically skipped questions about:
- BIOS-visible hardware status (RAM, HDD detection) since BIOS is inaccessible
- OS loading and network connectivity (since we can't even reach BIOS)
- Boot device detection (requires BIOS access)

### Example Session (All Mode)

```
$ python systemiq_cli.py all

Welcome to SystemIQ — Intelligent PC Hardware Troubleshooter!
Running in ALL mode: All questions will be asked for comprehensive analysis.
Answer the questions to receive ranked diagnoses with explanations.

[All diagnostic questions will be asked regardless of previous answers]
```

## Knowledge Base Structure

The knowledge base is located at `knowledge/knowledge_base.json` and consists of two main sections:

### Facts Section

Defines diagnostic facts (questions) and their valid answers:

```json
{
  "facts": {
    "power_led": {
      "question": "Is the power LED on? (yes/no): ",
      "answers": ["yes", "no"]
    },
    "bios_access": {
      "question": "Can you enter BIOS/UEFI setup? (yes/no): ",
      "answers": ["yes", "no"]
    }
    ...
  }
}
```

### Rules Section

Defines diagnostic rules with conditions, diagnosis labels, confidence factors, and explanations:

```json
{
  "rules": [
    {
      "id": "R1",
      "conditions": {"power_led": "no"},
      "diagnosis": "power_supply_failure",
      "cf": 0.96,
      "explanation": "No power LED strongly indicates PSU failure or no PSU output."
    }
    ...
  ]
}
```

## Smart Mode Logic

The smart mode implements conditional question dependencies to avoid asking illogical questions:

| Previous Answer | Questions Skipped | Reason |
|----------------|-------------------|--------|
| `power_led: no` | Most hardware questions | PC has no power - most diagnostics irrelevant |
| `bios_access: no` | `ram_status`, `hdd_status` | Cannot view hardware in BIOS |
| `display_output: no` | `artifacts` | Cannot see visual artifacts without display |
| `os_loads: no` | `blue_screen` (runtime) | OS never starts, so no runtime crashes |
| `fan_speed: stopped` | `high_noise` | Fans not spinning, so no noise |
| `os_loads: no` | `network_link` | Network requires OS to be running |
| `bios_access: no` | `usb_devices_fail` (if OS also fails) | Cannot test USB without BIOS or OS |

This logic can **reduce question count by 30-50%** while maintaining diagnostic accuracy.

## Extending the System

### Adding New Facts

1. Open `knowledge/knowledge_base.json`
2. Add a new fact definition in the `facts` section:

```json
"new_fact_name": {
  "question": "Your diagnostic question? (answer1/answer2): ",
  "answers": ["answer1", "answer2", "answer3"]
}
```

### Adding New Rules

Add a new rule in the `rules` section:

```json
{
  "id": "R21",
  "conditions": {
    "fact1": "value1",
    "fact2": "value2"
  },
  "diagnosis": "diagnosis_label",
  "cf": 0.85,
  "explanation": "Why these conditions suggest this diagnosis."
}
```

**Tips for effective rules:**
- Use confidence factors (cf) between 0.0 and 1.0
- Higher CF = stronger certainty of diagnosis
- Combine multiple symptoms for more specific diagnoses
- Write clear, actionable explanations

### Adjusting Smart Mode Logic

To modify question dependencies, edit the `should_ask_question()` function in `systemiq_cli.py`:

```python
def should_ask_question(facts: dict[str, str | None], fact: str, smart_mode: bool) -> bool:
    """Determine if a question should be asked based on previous answers."""
    if not smart_mode:
        return True
    
    # Add your conditional logic here
    if facts.get("some_fact") == "some_value":
        if fact in ["skip_this", "and_this"]:
            return False
    
    return True
```

## Technical Architecture

### Inference Engine
- **Forward chaining inference**: Questions are selected based on which facts could still satisfy unmatched rules
- **Prioritized question selection**: Facts that appear in more potential rules are asked first
- **Dynamic question filtering**: Smart mode skips questions that are logically impossible or irrelevant

### Confidence Factors
- Each rule has a CF between 0.0 and 1.0 indicating diagnostic certainty
- Multiple rules can fire for the same diagnosis
- Results are ranked by confidence for clear prioritization

### Knowledge Representation
- **Facts**: Observable symptoms and hardware states
- **Rules**: IF-THEN mappings from symptom combinations to diagnoses
- **Explanations**: Human-readable justifications for each diagnosis

## Diagnostic Categories

SystemIQ can diagnose issues across multiple hardware categories:

- **Power System**: PSU failures, power delivery issues
- **Cooling**: Fan failures, dust buildup, thermal issues
- **Memory**: RAM failures, seating issues, POST errors
- **Storage**: Drive failures, connection issues, bootloader problems
- **Display**: GPU failures, VRAM issues, display path problems
- **Motherboard**: Chipset issues, POST failures, USB controller problems
- **Operating System**: Boot failures, driver conflicts, corruption
- **Network**: Adapter failures, driver issues, connectivity problems

## Use Cases

### For Technicians
- Structured diagnostic workflow
- Documentation of troubleshooting steps
- Training tool for new technicians
- Consistent diagnostic approach

### For End Users
- Self-diagnosis before seeking professional help
- Understanding potential hardware issues
- Prioritizing repair actions by confidence

### For Researchers
- Knowledge base for hardware failure patterns
- Testing ground for expert system techniques
- Dataset for diagnostic AI training

## Contributing

To improve SystemIQ:

1. **Test diagnostics** against real hardware issues
2. **Refine confidence factors** based on real-world accuracy
3. **Add new rules** for additional failure modes
4. **Enhance conditional logic** for smarter question flow
5. **Expand explanations** for better user understanding
6. **Document edge cases** where the system needs improvement

## Known Limitations

- Does not diagnose software-specific issues beyond boot failures
- Cannot detect intermittent hardware failures
- Requires user to accurately assess hardware symptoms
- Limited to common PC hardware configurations
- May produce multiple diagnoses with similar confidence

## Future Improvements

- [ ] Web-based interface for remote diagnostics
- [ ] Diagnostic history and session logging
- [ ] Machine learning to refine confidence factors
- [ ] Integration with hardware monitoring tools
- [ ] Multi-language support
- [ ] Cloud-based knowledge base sharing

## License

This project is open source and available for educational and diagnostic purposes.

## Acknowledgments

Built using expert system principles and forward-chaining inference techniques. Knowledge base compiled from common PC hardware troubleshooting scenarios.

---

**SystemIQ** - Making PC diagnostics smarter, one question at a time.
