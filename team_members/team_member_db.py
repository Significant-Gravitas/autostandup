from typing import List, Tuple
from base_db import BaseDB

class TeamMemberDB(BaseDB):
    """
    TeamMemberDB class handles operations related to the 'team_members' table.
    """

    def __init__(self, host: str, user: str, password: str, database: str, port: str):
        """
        Initializes the TeamMemberDB class and creates the 'team_members' table if it doesn't exist.

        :param host: The MySQL host address.
        :param user: The MySQL user.
        :param password: The MySQL password.
        :param database: The MySQL database name.
        :param port: The MySQL port number.
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
                time_zone VARCHAR(50) NOT NULL
            );
        '''
        self.execute_query(query)

    def insert_new_member(self, discord_id: int, name: str, time_zone: str):
        """
        Inserts a new team member into the 'team_members' table.

        :param discord_id: The Discord ID of the team member.
        :param name: The name of the team member.
        :param time_zone: The time zone of the team member.
        """
        query = """
            INSERT INTO team_members (discord_id, name, time_zone)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE name = %s, time_zone = %s
        """
        params = (discord_id, name, time_zone, name, time_zone)
        self.execute_query(query, params)

    def remove_member(self, discord_id: int):
        """
        Removes a team member from the 'team_members' table.

        :param discord_id: The Discord ID of the team member to remove.
        """
        query = "DELETE FROM team_members WHERE discord_id = %s"
        params = (discord_id,)
        self.execute_query(query, params)

    def list_all_members(self) -> List[Tuple[int, str, str]]:
        """
        Fetches all team members from the 'team_members' table.

        :return: A list of tuples, each containing the Discord ID, name, and time zone of a team member.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor()
        c.execute("SELECT discord_id, name, time_zone FROM team_members")
        return c.fetchall()
