"""Base integration interface."""


class WorkoutIntegration:
    """Abstract base class for workout integrations."""

    def authenticate(self):
        """Authenticate with the service."""
        raise NotImplementedError

    def upload_workout(self, workout_name: str, workout_data: dict) -> str:
        """Upload a workout.

        Args:
            workout_name: Name of the workout
            workout_data: Provider-specific workout structure

        Returns:
            workout_id: Provider's workout ID
        """
        raise NotImplementedError

    def schedule_workout(self, workout_id: str, date: str):
        """Schedule a workout to a specific date.

        Args:
            workout_id: Provider's workout ID
            date: Date in YYYY-MM-DD format
        """
        raise NotImplementedError

    def delete_workout(self, workout_name: str) -> bool:
        """Delete a workout by name if it exists.

        Args:
            workout_name: Name of the workout to delete

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError
