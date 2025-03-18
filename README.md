# Automated Theorem Prover

This is an automated theorem prover, supporting first-order logic (FOL) with plans to add an induction schema and smart premise selection. Given arguments and a conclusion, it uses a resolution procedure to determine entailment. Currently, it's very much a work-in-progress.

## Development

Currently a WIP. To set up a virtual environment and run unit tests, run the following commands from the parent directory:
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `pytest`
