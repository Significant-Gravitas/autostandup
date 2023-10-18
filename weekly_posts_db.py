import datetime
from typing import Optional, Dict
from base_db import BaseDB

class WeeklyPostsDB(BaseDB):
    """
    Database class that handles operations related to the 'weekly_posts' table.
    """

    def __init__(self, host: str, user: str, password: str, database: str, port: str):
        """
        Initializes the WeeklyPostsDB class, connects to the MySQL database,
        and creates the 'weekly_posts' table if it doesn't exist.

        :param host: The MySQL host address.
        :param user: The MySQL user.
        :param password: The MySQL password.
        :param database: The MySQL database name.
        :param port: The MySQL port number.
        """
        super().__init__(host, user, password, database, port)
        self._create_weekly_posts_table()

    def _create_weekly_posts_table(self):
        """
        Creates the 'weekly_posts' table if it doesn't already exist.
        """
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS weekly_posts (
                post_id BIGINT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()

    def get_weekly_post_data(self) -> Optional[Dict[str, datetime.datetime]]:
        """
        Fetches the most recent weekly post data from the 'weekly_posts' table.

        :return: A dictionary containing the post ID and timestamp, or None if no data exists.
        """
        c = self.conn.cursor()
        c.execute("SELECT post_id, timestamp FROM weekly_posts LIMIT 1")
        row = c.fetchone()
        return {'post_id': row[0], 'timestamp': row[1]} if row else None

    def save_weekly_post_data(self, post_id: int, timestamp: datetime.datetime):
        """
        Inserts or updates the weekly post data in the 'weekly_posts' table.

        :param post_id: The ID of the weekly post.
        :param timestamp: The timestamp of the weekly post.
        """
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO weekly_posts (post_id, timestamp)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE timestamp = %s
        """, (post_id, timestamp, timestamp))
        self.conn.commit()
