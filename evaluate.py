#!/usr/bin/env python3
"""
Root runner for OmniTech AI Capstone Evaluation.
Usage:
    python evaluate.py
"""
from eval.evaluate import run_evaluation, print_evaluation_report

if __name__ == "__main__":
    results = run_evaluation()
    print_evaluation_report(results)
