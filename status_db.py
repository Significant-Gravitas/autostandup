import mysql.connector
from typing import List, Tuple

class StatusDB:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        
        # Create Users Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                time_zone VARCHAR(50) NOT NULL
            );
        ''')
        
        # Create Updates Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discord_id INT,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES users(discord_id)
            );
        ''')
        
        # Create Streaks Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                discord_id INT PRIMARY KEY,
                current_streak INT DEFAULT 0,
                FOREIGN KEY (discord_id) REFERENCES users(discord_id)
            );
        ''')
        
        self.conn.commit()

    def insert_status(self, discord_id: int, name: str, status: str):
        """Inserts a new status update into the 'updates' table."""
        c = self.conn.cursor()
        c.execute("INSERT INTO updates (discord_id, name, status) VALUES (%s, %s, %s)",
                  (discord_id, name, status))
        self.conn.commit()

    def get_all_statuses(self) -> List[Tuple[int, str, str, str]]:
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
        c.execute("INSERT OR REPLACE INTO team_members (discord_id, name, time_zone) VALUES (%s, %s, %s)",
                  (discord_id, name, time_zone))
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
