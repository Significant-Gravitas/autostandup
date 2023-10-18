import mysql.connector

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
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )

    def close(self):
        """
        Closes the MySQL database connection.
        """
        self.conn.close()