from base_db import BaseDB

class StreaksDB(BaseDB):
    """
    StreaksDB class handles all operations related to the 'streaks' table.
    Inherits from the BaseDB class.
    """

    def __init__(self, host, user, password, database, port):
        """
        Initializes the StreaksDB class and creates the 'streaks' table if it doesn't exist.

        :param host: The MySQL host address.
        :param user: The MySQL user.
        :param password: The MySQL password.
        :param database: The MySQL database name.
        :param port: The MySQL port number.
        """
        super().__init__(host, user, password, database, port)
        self._create_streaks_table()

    def _create_streaks_table(self):
        """
        Creates the 'streaks' table if it doesn't already exist.
        """
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                discord_id BIGINT PRIMARY KEY,
                current_streak INT DEFAULT 0,
                FOREIGN KEY (discord_id) REFERENCES team_members(discord_id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    def update_streak(self, discord_id: int, new_streak: int):
        """
        Updates the streak for a given user.

        :param discord_id: The Discord ID of the user.
        :param new_streak: The new streak count.
        """
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO streaks (discord_id, current_streak)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE current_streak = %s
        """, (discord_id, new_streak, new_streak))
        self.conn.commit()

    def get_streak(self, discord_id: int) -> int:
        """
        Fetches the current streak for a given user.

        :param discord_id: The Discord ID of the user.
        :return: The current streak count.
        """
        c = self.conn.cursor()
        c.execute("SELECT current_streak FROM streaks WHERE discord_id = %s", (discord_id,))
        row = c.fetchone()
        return row[0] if row else 0
