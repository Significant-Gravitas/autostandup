from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Tuple
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
                time_zone VARCHAR(255),
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id) ON DELETE CASCADE
            )
        '''
        try:
            self.execute_query(query)
        finally:
            self.close()

    def insert_status(self, discord_id: int, status: str, time_zone: str):
        """
        Inserts a new status update into the 'updates' table.

        :param discord_id: The Discord ID of the team member.
        :param status: The status update.
        :param time_zone: The time zone of the user.
        """
        # Convert current UTC time to user's local time zone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        local_now = utc_now.astimezone(pytz.timezone(time_zone))

        query = "INSERT INTO updates (discord_id, status, timestamp, time_zone) VALUES (%s, %s, %s, %s)"
        params = (discord_id, status, local_now, time_zone)
        try:
            self.execute_query(query, params)
        finally:
            self.close()

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
        try:
            self.execute_query(query, params)
        finally:
            self.close()
        
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
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

        query = """
            SELECT COUNT(*) FROM updates
            WHERE discord_id = %s AND timestamp >= %s
        """
        params = (discord_id, monday)
        try:
            c.execute(query, params)
            
            row = c.fetchone()
            return row[0] if row else 0
        finally:
            c.close()
            self.close()

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
        try:
            c.execute(query, params)
            
            statuses = [row[0] for row in c.fetchall()]
            return statuses
        finally:
            c.close()
            self.close()
    
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
        try:
            c.execute(query, params)
            
            statuses = c.fetchall()
            return statuses
        finally:
            c.close()
            self.close()
    
    def get_last_update_timestamp(self, discord_id: int) -> Tuple[datetime, str]:
        """
        Fetches the timestamp and time zone of the last status update for a given user.

        Args:
            discord_id: The Discord ID of the user.

        Returns:
            A tuple containing the timestamp of the last update and its time zone, or (None, None) if there are no updates.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor()
        
        query = """
            SELECT timestamp, time_zone FROM updates
            WHERE discord_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        params = (discord_id,)
        try:
            c.execute(query, params)
            
            row = c.fetchone()
            return (row[0], row[1]) if row else (None, None)
        finally:
            c.close()
            self.close()
    
    def delete_newest_status(self, discord_id: int) -> None:
        """
        Deletes the most recent status update for a given user.

        Args:
            discord_id: The Discord ID of the user.
        """
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        c = self.conn.cursor()
        
        # Fetch the ID of the newest status update for the given user
        query_get_id = """
            SELECT id FROM updates
            WHERE discord_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        try:
            c.execute(query_get_id, (discord_id,))
            
            row = c.fetchone()
            if row:
                status_id = row[0]
                
                # Now, delete the status update using its ID
                query_delete = """
                    DELETE FROM updates WHERE id = %s
                """
                c.execute(query_delete, (status_id,))
                
                self.conn.commit()
        finally:
            c.close()
            self.close()
