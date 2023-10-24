from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any
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
        query = '''
            CREATE TABLE IF NOT EXISTS updates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discord_id BIGINT,
                status TEXT NOT NULL,
                summarized_status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id) ON DELETE CASCADE
            )
        '''
        self.execute_query(query)

    def insert_status(self, discord_id: int, status: str):
        """
        Inserts a new status update into the 'updates' table.

        :param discord_id: The Discord ID of the team member.
        :param status: The status update.
        """
        query = "INSERT INTO updates (discord_id, status) VALUES (%s, %s)"
        params = (discord_id, status)
        self.execute_query(query, params)

    def update_summarized_status(self, discord_id: int, summarized_status: str):
        """
        Updates the summarized_status for the most recent update for a given user.

        :param discord_id: The Discord ID of the team member.
        :param summarized_status: The summarized status update.
        """
        query = """
            UPDATE updates
            SET summarized_status = %s
            WHERE discord_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        params = (summarized_status, discord_id)
        self.execute_query(query, params)
        
    def get_weekly_checkins_count(self, discord_id: int, time_zone: str) -> int:
        """
        Fetches the number of check-ins for a given user in the current week.

        :param discord_id: The Discord ID of the user.
        :param time_zone: The time zone of the user.
        :return: The count of check-ins in the current week.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor()
        
        # Adjusting the current time to the user's time zone
        local_tz = pytz.timezone(time_zone)
        local_now = datetime.now(local_tz)
        
        # Getting the Monday of the current week in the user's time zone
        monday = local_now - timedelta(days=local_now.weekday())
        monday = local_now.replace(hour=0, minute=0, second=0, microsecond=0)  # set time to 00:00:00 for accurate comparison

        query = """
            SELECT COUNT(*) FROM updates
            WHERE discord_id = %s AND timestamp >= %s
        """
        params = (discord_id, monday)
        c.execute(query, params)
        
        row = c.fetchone()
        return row[0] if row else 0

    def get_statuses_in_date_range(self, discord_id: int, start_date: datetime, end_date: datetime) -> List[str]:
        """
        Fetches all raw status updates for a given user within a specified date range.

        Args:
            discord_id: The Discord ID of the user.
            start_date: The start date of the date range.
            end_date: The end date of the date range.

        Returns:
            A list of raw status updates.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor()
        
        query = """
            SELECT summarized_status FROM updates
            WHERE discord_id = %s AND timestamp >= %s AND timestamp <= %s
        """
        params = (discord_id, start_date, end_date)
        c.execute(query, params)
        
        statuses = [row[0] for row in c.fetchall()]
        return statuses
    
    def get_all_statuses_for_user(self, discord_id: int) -> List[dict]:
        """
        Fetches all status updates (both raw and summarized) for a given user.

        Args:
            discord_id: The Discord ID of the user.

        Returns:
            A list of dictionaries, each containing the status update details for a given record.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor(dictionary=True)  # Set dictionary=True to return results as dictionaries
        
        query = """
            SELECT id, discord_id, status, summarized_status, timestamp 
            FROM updates
            WHERE discord_id = %s
            ORDER BY timestamp DESC
        """
        params = (discord_id,)
        c.execute(query, params)
        
        statuses = c.fetchall()
        return statuses
    