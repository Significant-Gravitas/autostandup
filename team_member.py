class TeamMember:
    def __init__(self, discord_id: int, time_zone: str, name: str) -> None:
        self.discord_id: int = discord_id
        self.time_zone: str = time_zone
        self.name: str = name