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
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
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

    def close(self):
        """Closes the SQLite database connection."""
        self.conn.close()
