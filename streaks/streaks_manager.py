from streaks.streaks_db import StreaksDB

class StreaksManager:
    """
    Manages the streaks for team members.
    """
    
    def __init__(self, streaks_db: StreaksDB):
        """
        Initializes a new StreaksManager instance.

        Args:
            streaks_db: The StreaksDB object that handles database operations.
        """
        self.streaks_db = streaks_db
    
    def get_streak(self, discord_id: int) -> int:
        """
        Fetches the current streak for a given user.

        Args:
            discord_id: The Discord ID of the user.

        Returns:
            The current streak count.
        """
        return self.streaks_db.get_streak(discord_id)

    def update_streak(self, discord_id: int, new_streak: int):
        """
        Updates the streak for a given user.

        Args:
            discord_id: The Discord ID of the user.
            new_streak: The new streak count.
        """
        self.streaks_db.update_streak(discord_id, new_streak)
        
    def reset_streak(self, discord_id: int):
        """
        Resets the streak for a given user to zero.

        Args:
            discord_id: The Discord ID of the user.
        """
        self.streaks_db.update_streak(discord_id, 0)