class TeamMember:
    """TeamMember class to store individual team member details.
    
    Attributes:
        discord_id: The Discord ID of the team member.
        time_zone: The time zone in which the team member resides.
        name: The name of the team member.
    """
    
    def __init__(self, discord_id: int, time_zone: str, name: str) -> None:
        """Initialize a new TeamMember object.
        
        Args:
            discord_id: The Discord ID of the team member.
            time_zone: The time zone of the team member.
            name: The name of the team member.
        """
        self.discord_id: int = discord_id
        self.time_zone: str = time_zone
        self.name: str = name