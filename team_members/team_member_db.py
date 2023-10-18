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
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                discord_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                time_zone VARCHAR(50) NOT NULL
            );
        ''')
        self.conn.commit()

    def insert_new_member(self, discord_id: int, name: str, time_zone: str):
        """
        Inserts a new team member into the 'team_members' table.

        :param discord_id: The Discord ID of the team member.
        :param name: The name of the team member.
        :param time_zone: The time zone of the team member.
        """
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO team_members (discord_id, name, time_zone)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE name = %s, time_zone = %s
        """, (discord_id, name, time_zone, name, time_zone))
        self.conn.commit()

    def remove_member(self, discord_id: int):
        """
        Removes a team member from the 'team_members' table.

        :param discord_id: The Discord ID of the team member to remove.
        """
        c = self.conn.cursor()
        c.execute("DELETE FROM team_members WHERE discord_id = %s", (discord_id,))
        self.conn.commit()

    def list_all_members(self) -> List[Tuple[int, str, str]]:
        """
        Fetches all team members from the 'team_members' table.

        :return: A list of tuples, each containing the Discord ID, name, and time zone of a team member.
        """
        c = self.conn.cursor()
        c.execute("SELECT discord_id, name, time_zone FROM team_members")
        return c.fetchall()
