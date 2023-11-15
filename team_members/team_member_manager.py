from typing import List
from team_members.team_member import TeamMember
from team_members.team_member_db import TeamMemberDB

class TeamMemberManager:
    """
    Manages operations related to team members.
    """

    def __init__(self, db: TeamMemberDB):
        """
        Initialize a TeamMemberManager object.

        :param db: TeamMemberDB object for interacting with the database.
        """
        self.db = db
        self.team_members = self.load_team_members()

    def load_team_members(self) -> List[TeamMember]:
        """
        Load team members from the MySQL database into a list of TeamMember objects.

        :return: List of TeamMember objects.
        """
        team_members = []
        members_data = self.db.list_all_members()

        for member_data in members_data:
            member = TeamMember(
                discord_id=member_data[0],
                time_zone=member_data[2],
                name=member_data[1],
                github_username=member_data[3],
                on_vacation=member_data[4]
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

    def add_member(self, discord_id: int, name: str, time_zone: str, github_username: str):
        """
        Add a new team member to the list and the database.

        :param discord_id: The Discord ID of the new member.
        :param name: The name of the new member.
        :param time_zone: The time zone of the new member.
        :param github_username: The GitHub username of the new member.
        """
        new_member = TeamMember(discord_id, time_zone, name, github_username)
        self.db.insert_new_member(discord_id, name, time_zone, github_username)
        self.team_members.append(new_member)

    def remove_member(self, discord_id: int):
        """
        Remove a team member from the list and the database.

        :param discord_id: The Discord ID of the member to remove.
        """
        self.db.remove_member(discord_id)
        self.team_members = [member for member in self.team_members if member.discord_id != discord_id]

    def update_member_timezone(self, discord_id: int, new_time_zone: str):
        """
        Update the timezone of a team member in the database and the list.

        :param discord_id: The Discord ID of the member to update.
        :param new_time_zone: The new timezone string to set for the member.
        """
        # Update the timezone in the database
        self.db.update_member_timezone(discord_id, new_time_zone)

        # Find the member in the team_members list and update their timezone
        member = self.find_member(discord_id)
        if member:
            member.time_zone = new_time_zone

    def set_member_vacation_status(self, discord_id: int, on_vacation: bool):
        """
        Sets the vacation status of a team member.

        :param discord_id: The Discord ID of the team member.
        :param on_vacation: The vacation status to be set for the team member.
        """
        # Update the vacation status in the database
        self.db.set_vacation_status(discord_id, on_vacation)

        # Find the member in the team_members list and update their vacation status
        member = self.find_member(discord_id)
        if member:
            member.on_vacation = on_vacation