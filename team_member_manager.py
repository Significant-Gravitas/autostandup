import json
from typing import List
from team_member import TeamMember

class TeamMemberManager:
    """
    Manages operations related to team members.
    """

    def __init__(self, team_members_json_path: str):
        """
        Initialize a TeamMemberManager object.

        :param team_members_json_path: Path to the JSON file containing team member data.
        """
        self.team_members_json_path = team_members_json_path
        self.team_members = self.load_team_members()

    def load_team_members(self) -> List[TeamMember]:
        """
        Load team members from a JSON file into a list of TeamMember objects.

        :return: List of TeamMember objects.
        """
        team_members = []
        with open(self.team_members_json_path, "r") as f:
            team_members_data = json.load(f)

        for member_data in team_members_data:
            member = TeamMember(
                discord_id=member_data["discord_id"],
                time_zone=member_data["time_zone"],
                name=member_data["name"]
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
