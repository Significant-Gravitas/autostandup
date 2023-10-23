from typing import List, Tuple
from updates.updates_db import UpdatesDB

class UpdatesManager:
    """
    Manages status updates for team members.
    """

    def __init__(self, updates_db: UpdatesDB):
        """
        Initializes a new UpdatesManager instance.

        Args:
            updates_db: The UpdatesDB object that handles database operations.
        """
        self.updates_db = updates_db

    def insert_status(self, discord_id: int, status: str):
        """
        Inserts a new status update.

        Args:
            discord_id: The Discord ID of the team member.
            status: The status update.
        """
        self.updates_db.insert_status(discord_id, status)

    def update_summarized_status(self, discord_id: int, summarized_status: str):
        """
        Updates the summarized status for the most recent update for a given user.

        Args:
            discord_id: The Discord ID of the team member.
            summarized_status: The summarized status update.
        """
        self.updates_db.update_summarized_status(discord_id, summarized_status)

    def get_weekly_checkins_count(self, discord_id: int, time_zone: str) -> int:
        """
        Fetches the number of check-ins for a given user in the current week.

        Args:
            discord_id: The Discord ID of the user.
            time_zone: The time zone of the user.

        Returns:
            The count of check-ins in the current week.
        """
        return self.updates_db.get_weekly_checkins_count(discord_id, time_zone)
