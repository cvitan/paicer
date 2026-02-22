"""Base formatter interface."""


class DocumentFormatter:
    """Abstract base class for document formatters."""

    def render(self, plan_data: dict) -> str:
        """Render plan data to formatted output.

        Args:
            plan_data: Complete plan data from YAML

        Returns:
            Formatted string output
        """
        raise NotImplementedError
