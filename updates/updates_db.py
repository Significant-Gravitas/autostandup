from typing import List, Tuple
from base_db import BaseDB

class UpdatesDB(BaseDB):
    """
    Database class for handling operations related to the 'updates' table.
    """

    def __init__(self, host: str, user: str, password: str, database: str, port: str):
        """
        Initializes the UpdatesDB class and creates the 'updates' table if it doesn't exist.

        :param host: The MySQL host address.
        :param user: The MySQL user.
        :param password: The MySQL password.
        :param database: The MySQL database name.
        :param port: The MySQL port number.
        """
        super().__init__(host, user, password, database, port)
        self._create_updates_table()

    def _create_updates_table(self):
        """
        Creates the 'updates' table if it doesn't already exist.
        """
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discord_id BIGINT,
                status TEXT NOT NULL,
                summarized_status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    def insert_status(self, discord_id: int, status: str):
        """
        Inserts a new status update into the 'updates' table.

        :param discord_id: The Discord ID of the team member.
        :param status: The status update.
        """
        c = self.conn.cursor()
        c.execute("INSERT INTO updates (discord_id, status) VALUES (%s, %s)",
                  (discord_id, status))
        self.conn.commit()

    def update_summarized_status(self, discord_id: int, summarized_status: str):
        """
        Updates the summarized_status for the most recent update for a given user.

        :param discord_id: The Discord ID of the team member.
        :param summarized_status: The summarized status update.
        """
        c = self.conn.cursor()
        c.execute("""
            UPDATE updates
            SET summarized_status = %s
            WHERE discord_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (summarized_status, discord_id))
        self.conn.commit()

    def get_all_statuses(self) -> List[Tuple[int, str, str]]:
        """
        Fetches all status updates from the 'updates' table.

        :return: List of tuples containing Discord ID, status, and timestamp.
        """
        c = self.conn.cursor()
        c.execute("SELECT discord_id, status, timestamp FROM updates")
        return c.fetchall()
