# SystemIQ — Intelligent PC Hardware Troubleshooter

SystemIQ is an interactive, explainable expert system for diagnosing PC hardware and boot issues using a **knowledge base of facts + rules + confidence factors**.

## What changed

- All troubleshooting knowledge is now externalized in `knowledge/knowledge_base.json`.
- The CLI loads facts/questions and rules from JSON at startup.
- You can now extend the system by editing JSON, without changing Python logic.

## Run

```bash
python3 systemiq_cli.py
```

## Knowledge base location

- `knowledge/knowledge_base.json`
  - `facts` section defines each fact's question and valid answers.
  - `rules` section defines rule `id`, `conditions`, `diagnosis`, `cf`, and `explanation`.
