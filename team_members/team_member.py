class TeamMember:
    """TeamMember class to store individual team member details.
    
    Attributes:
        discord_id: The Discord ID of the team member.
        time_zone: The time zone in which the team member resides.
        name: The name of the team member.
        current_streak: The current streak of daily updates/check-ins of the team member.
        weekly_checkins: The number of check-ins for the current week.
    """
    
    def __init__(self, discord_id: int, time_zone: str, name: str,
                 current_streak: int = 0, weekly_checkins: int = 0) -> None:
        """Initialize a new TeamMember object.
        
        Args:
            discord_id: The Discord ID of the team member.
            time_zone: The time zone of the team member.
            name: The name of the team member.
            current_streak: The current streak of daily updates/check-ins. Defaults to 0.
            weekly_checkins: The number of check-ins for the current week. Defaults to 0.
        """
        self.discord_id: int = discord_id
        self.time_zone: str = time_zone
        self.name: str = name
        self.current_streak: int = current_streak
        self.weekly_checkins: int = weekly_checkins
    
    def update_streak(self, streak: int) -> None:
        """Update the current streak of the team member.
        
        Args:
            streak: The new streak count.
        """
        self.current_streak = streak
    
    def reset_streak(self) -> None:
        """Reset the current streak of the team member to 0."""
        self.current_streak = 0
    
    def increment_weekly_checkins(self) -> None:
        """Increment the number of check-ins for the current week by 1."""
        self.weekly_checkins += 1
    
    def reset_weekly_checkins(self) -> None:
        """Reset the number of check-ins for the current week to 0."""
        self.weekly_checkins = 0