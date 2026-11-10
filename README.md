# MedSEO — archived demonstration

This repository is a synthetic-data analytics demonstration, not a deployed Google ranking measurement or trained AI agent. Continue production development in [teraj-stack/bmclinic.co](https://github.com/teraj-stack/bmclinic.co).

The medical paragraph generator is disabled because it applied a fixed procedure description to arbitrary procedure names. The telemetry endpoint returns HTTP 410 instead of falsely claiming persistence. Re-running the Python seed preserves existing rows and skips seeding when records exist.

Do not deploy this dashboard as the patient website. Historical figures, credentials, scores and conclusions are examples, not clinic evidence. The `public/agent_knowledge_state.json` file contains demonstration output.

Regression check: `python3 tests/test_seed.py`.
