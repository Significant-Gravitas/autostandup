import mysql.connector
from mysql.connector import errors

class BaseDB:
    """
    Base Database class that handles the MySQL database connection.
    """

    def __init__(self, host: str, user: str, password: str, database: str, port: str):
        """
        Initializes the BaseDB class and connects to the MySQL database.

        :param host: The MySQL host address.
        :param user: The MySQL user.
        :param password: The MySQL password.
        :param database: The MySQL database name.
        :param port: The MySQL port number.
        """
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port
        }
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
        except errors.InterfaceError as e:
            print(f"Error connecting to MySQL: {e}")
            # You can add retry logic or other error handling here if needed

    def close(self):
        """
        Closes the MySQL database connection.
        """
        self.conn.close()

    def execute_query(self, query, params=None):
        if not self.conn.is_connected():
            print("Reconnecting to MySQL")
            self.connect()

        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            self.conn.commit()
        except errors.OperationalError as e:
            print(f"MySQL operational error: {e}")
            self.conn.rollback()
        finally:
            cursor.close()
