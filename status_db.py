import sqlite3
from typing import List, Tuple

class StatusDB:
    """StatusDB class for managing SQLite database operations.
    
    Attributes:
        conn: The SQLite database connection.
    """
    
    def __init__(self, db_name: str = 'status_updates.db'):
        """Initializes the StatusDB object and database connection."""
        self.conn = sqlite3.connect(db_name)
        self._create_table()

    def _create_table(self):
        """Creates the 'updates' table if it doesn't exist."""
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                streak INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create team_members table
        c.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                discord_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                time_zone TEXT NOT NULL
            );
        ''')

        self.conn.commit()

    def insert_status(self, discord_id: int, name: str, status: str):
        """Inserts a new status update into the 'updates' table.

        Args:
            discord_id: The Discord ID of the user.
            name: The name of the user.
            status: The status message to insert.
        """
        c = self.conn.cursor()
        c.execute("INSERT INTO updates (discord_id, name, status) VALUES (?, ?, ?)",
                  (discord_id, name, status))
        self.conn.commit()

    def get_all_statuses(self) -> List[Tuple[int, str, str, str]]:
        """Fetches all status updates from the 'updates' table.

        Returns:
            A list of tuples containing Discord ID, name, status, and timestamp.
        """
        c = self.conn.cursor()
        c.execute("SELECT discord_id, name, status, timestamp FROM updates")
        return c.fetchall()
    
    def update_streak(self, discord_id: int, new_streak: int):
        """Updates the streak for a given user."""
        c = self.conn.cursor()
        c.execute("UPDATE updates SET streak = ? WHERE discord_id = ?", (new_streak, discord_id))
        self.conn.commit()

    def get_streak(self, discord_id: int) -> int:
        """Fetches the current streak for a given user."""
        c = self.conn.cursor()
        c.execute("SELECT streak FROM updates WHERE discord_id = ?", (discord_id,))
        row = c.fetchone()
        return row[0] if row else 0

    def close(self):
        """Closes the SQLite database connection."""
        self.conn.close()

    def insert_new_member(self, discord_id: int, name: str, time_zone: str):
        """Inserts a new team member into the 'team_members' table."""
        try:
            c = self.conn.cursor()
            c.execute("INSERT OR REPLACE INTO team_members (discord_id, name, time_zone) VALUES (?, ?, ?)",
                    (discord_id, name, time_zone))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def remove_member(self, discord_id: int):
        """Removes a team member from the 'team_members' table."""
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM team_members WHERE discord_id = ?", (discord_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def list_all_members(self) -> List[Tuple[int, str, str]]:
        """Fetches all team members from the 'team_members' table.

        Returns:
            A list of tuples containing Discord ID, name, and time_zone.
        """
        try:
            c = self.conn.cursor()
            c.execute("SELECT discord_id, name, time_zone FROM team_members")
            return c.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
