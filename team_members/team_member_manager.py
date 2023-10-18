from typing import List
from team_member import TeamMember
from team_member_db import TeamMemberDB

class TeamMemberManager:
    """
    Manages operations related to team members.
    """

    def __init__(self, db: TeamMemberDB):
        """
        Initialize a TeamMemberManager object.

        :param db: StatusDB object for interacting with the database.
        """
        self.db = db
        self.team_members = self.load_team_members()

    def load_team_members(self) -> List[TeamMember]:
        """
        Load team members from the SQLite database into a list of TeamMember objects.

        :return: List of TeamMember objects.
        """
        team_members = []
        members_data = self.db.list_all_members()

        for member_data in members_data:
            member = TeamMember(
                discord_id=member_data[0],
                time_zone=member_data[2],
                name=member_data[1]
            )
            team_members.append(member)

        return team_members

    def find_member(self, discord_id: int) -> TeamMember:
        """
        Find and return a team member by their Discord ID.

        :param discord_id: The Discord ID of the team member.
        :return: A TeamMember object if found, otherwise None.
        """
        for member in self.team_members:
            if member.discord_id == discord_id:
                return member
        return None

    def add_member(self, discord_id: int, name: str, time_zone: str):
        """
        Add a new team member to the list and the database.

        :param discord_id: The Discord ID of the new member.
        :param name: The name of the new member.
        :param time_zone: The time zone of the new member.
        """
        new_member = TeamMember(discord_id, time_zone, name)
        self.db.insert_new_member(discord_id, name, time_zone)
        self.team_members.append(new_member)

    def remove_member(self, discord_id: int):
        """
        Remove a team member from the list and the database.

        :param discord_id: The Discord ID of the member to remove.
        """
        self.db.remove_member(discord_id)
        self.team_members = [member for member in self.team_members if member.discord_id != discord_id]