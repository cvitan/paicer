import sys
from .plan_utils import load_plan, validate_training_days
from .formatters.markdown import MarkdownFormatter
from .formatters.html import HTMLFormatter


def render_plan(plan_file: str, html: bool = False, paper_format: str = "a4") -> str:
    """Load plan and render to string. Raises SystemExit on validation errors."""
    data = load_plan(plan_file)
    errors = validate_training_days(data)
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if html:
        return HTMLFormatter(paper_format).render(data)
    return MarkdownFormatter().render(data)
