from typing import List, Tuple
from base_db import BaseDB

class TeamMemberDB(BaseDB):
    """
    TeamMemberDB class handles operations related to the 'team_members' table.

    :param host: The MySQL host address.
    :param user: The MySQL user.
    :param password: The MySQL password.
    :param database: The MySQL database name.
    :param port: The MySQL port number.
    """

    def __init__(self, host: str, user: str, password: str, database: str, port: str):
        """
        Initializes the TeamMemberDB class and creates the 'team_members' table if it doesn't exist.
        """
        super().__init__(host, user, password, database, port)
        self._create_team_members_table()

    def _create_team_members_table(self):
        """
        Creates the 'team_members' table if it doesn't already exist.
        """
        query = '''
            CREATE TABLE IF NOT EXISTS team_members (
                discord_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                time_zone VARCHAR(50) NOT NULL,
                github_username VARCHAR(255),
                on_vacation BOOLEAN DEFAULT FALSE
            );
        '''
        try:
            self.execute_query(query)
        finally:
            self.close()

    def insert_new_member(self, discord_id: int, name: str, time_zone: str, github_username: str):
        """
        Inserts a new team member into the 'team_members' table.

        :param discord_id: The Discord ID of the team member.
        :param name: The name of the team member.
        :param time_zone: The time zone of the team member.
        :param github_username: The GitHub username of the team member.
        """
        query = """
            INSERT INTO team_members (discord_id, name, time_zone, github_username)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name = %s, time_zone = %s, github_username = %s
        """
        params = (discord_id, name, time_zone, github_username, name, time_zone, github_username)
        try:
            self.execute_query(query, params)
        finally:
            self.close()

    def remove_member(self, discord_id: int):
        """
        Removes a team member from the 'team_members' table.

        :param discord_id: The Discord ID of the team member to remove.
        """
        query = "DELETE FROM team_members WHERE discord_id = %s"
        params = (discord_id,)
        try:
            self.execute_query(query, params)
        finally:
            self.close()

    def list_all_members(self) -> List[Tuple[int, str, str, str, bool]]:
        """
        Fetches all team members from the 'team_members' table.

        :return: A list of tuples, each containing the Discord ID, name, time zone, GitHub username, and vacation status of a team member.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()
        c = self.conn.cursor()
        try:
            c.execute("SELECT discord_id, name, time_zone, github_username, on_vacation FROM team_members")
            return c.fetchall()
        finally:
            c.close()
            self.close()

    def update_member_timezone(self, discord_id: int, new_time_zone: str):
        """
        Updates the timezone of a team member in the 'team_members' table.

        :param discord_id: The Discord ID of the team member.
        :param new_time_zone: The new timezone to be set for the team member.
        """
        query = "UPDATE team_members SET time_zone = %s WHERE discord_id = %s"
        params = (new_time_zone, discord_id)
        try:
            self.execute_query(query, params)
        finally:
            self.close()

    def set_vacation_status(self, discord_id: int, on_vacation: bool):
        """
        Sets the vacation status of a team member in the 'team_members' table.

        :param discord_id: The Discord ID of the team member.
        :param on_vacation: The vacation status to be set for the team member.
        """
        query = "UPDATE team_members SET on_vacation = %s WHERE discord_id = %s"
        params = (on_vacation, discord_id)
        try:
            self.execute_query(query, params)
        finally:
            self.close()