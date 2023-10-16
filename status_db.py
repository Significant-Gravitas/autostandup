import datetime
import mysql.connector
from typing import List, Tuple

# TODO: Break this into different databases
class StatusDB:
    def __init__(self, host, user, password, database, port):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        
        # Create team_members Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                discord_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                time_zone VARCHAR(50) NOT NULL
            );
        ''')
        
        # Create Updates Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discord_id BIGINT,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id)
            );
        ''')
        
        # Create Streaks Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                discord_id BIGINT PRIMARY KEY,
                current_streak INT DEFAULT 0,
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id)
            );
        ''')

        # Create Weekly Posts Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS weekly_posts (
                post_id BIGINT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        self.conn.commit()

    def insert_status(self, discord_id: int, status: str):
        """Inserts a new status update into the 'updates' table."""
        c = self.conn.cursor()
        c.execute("INSERT INTO updates (discord_id, status) VALUES (%s, %s)",
                  (discord_id, status))
        self.conn.commit()

    def get_all_statuses(self) -> List[Tuple[int, str, str]]:
        """Fetches all status updates from the 'updates' table."""
        c = self.conn.cursor()
        c.execute("SELECT discord_id, status, timestamp FROM updates")
        return c.fetchall()

    def update_streak(self, discord_id: int, new_streak: int):
        """Updates the streak for a given user."""
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO streaks (discord_id, current_streak)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE current_streak = %s
        """, (discord_id, new_streak, new_streak))
        self.conn.commit()

    def get_streak(self, discord_id: int) -> int:
        """Fetches the current streak for a given user."""
        c = self.conn.cursor()
        c.execute("SELECT current_streak FROM streaks WHERE discord_id = %s", (discord_id,))
        row = c.fetchone()
        return row[0] if row else 0

    def close(self):
        """Closes the MySQL database connection."""
        self.conn.close()

    def insert_new_member(self, discord_id: int, name: str, time_zone: str):
        """Inserts a new team member into the 'team_members' table."""
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO team_members (discord_id, name, time_zone)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE name = %s, time_zone = %s
        """, (discord_id, name, time_zone, name, time_zone))
        self.conn.commit()

    def remove_member(self, discord_id: int):
        """Removes a team member from the 'team_members' table."""
        c = self.conn.cursor()
        c.execute("DELETE FROM team_members WHERE discord_id = %s", (discord_id,))
        self.conn.commit()

    def list_all_members(self) -> List[Tuple[int, str, str]]:
        """Fetches all team members from the 'team_members' table."""
        c = self.conn.cursor()
        c.execute("SELECT discord_id, name, time_zone FROM team_members")
        return c.fetchall()

    def get_weekly_post_data(self):
        c = self.conn.cursor()
        c.execute("SELECT post_id, timestamp FROM weekly_posts LIMIT 1")
        row = c.fetchone()
        return {'post_id': row[0], 'timestamp': row[1]} if row else {}

    def save_weekly_post_data(self, post_id: int, timestamp: datetime):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO weekly_posts (post_id, timestamp)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE timestamp = %s
        """, (post_id, timestamp, timestamp))
        self.conn.commit()

