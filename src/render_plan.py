#!/usr/bin/env python3
"""
Render training plan in different formats (Markdown or HTML).

Usage:
    python render_plan.py plan.yaml > training_plan.md
    python render_plan.py plan.yaml --html > training_plan.html
    python render_plan.py plan.yaml --html --format=a4 > training_plan.html
"""

import sys
from plan_utils import load_plan, validate_training_days
from formatters.markdown import MarkdownFormatter
from formatters.html import HTMLFormatter


def main():
    if len(sys.argv) < 2:
        print("Usage: python render_plan.py plan.yaml [--html] [--format=a4|letter]")
        sys.exit(1)

    plan_file = sys.argv[1]
    output_html = "--html" in sys.argv

    # Parse format parameter
    paper_format = "a4"  # Default (metric); Makefile passes letter for imperial
    for arg in sys.argv:
        if arg.startswith("--format="):
            paper_format = arg.split("=")[1].lower()
            if paper_format not in ["a4", "letter"]:
                print(f"Invalid format: {paper_format}. Use 'a4' or 'letter'")
                sys.exit(1)

    # Load and validate plan
    data = load_plan(plan_file)
    errors = validate_training_days(data)
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Render using appropriate formatter
    if output_html:
        formatter = HTMLFormatter(paper_format)
    else:
        formatter = MarkdownFormatter()

    output = formatter.render(data)
    print(output)


if __name__ == "__main__":
    main()
