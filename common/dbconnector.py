import pymysql
import configparser


class dbConnector():
    def __init__(self, config_file):
        '''
        Loads connection settings from config file, section database
        :param config_file: configuration file
        '''
        config = configparser.ConfigParser()
        config.read(config_file)
        self.__connection_settings = config['database']

    def open(self):
        '''
        Connects to the database
        '''
        self.conn = pymysql.connect(host=self.__connection_settings['host'],
                                    port=int(self.__connection_settings['port']),
                                    user=self.__connection_settings['user'],
                                    passwd=self.__connection_settings['passwd'],
                                    db=self.__connection_settings['db'])
        self.cursor = self.conn.cursor()

    def close(self):
        '''
        Closes database connection
        '''
        self.cursor.close()
        self.conn.close()

    def get_row(self, sql):
        '''
        Get first array with the first row results from executing query.
        Returns None if there are no results.

        :param sql: SELECT statement
        '''
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def insert_row(self, sql):
        '''
        Inserts a row and returns the value of column id of the new row
        Returns None if query fails

        :param sql: INSERT statement
        '''
        new_id = None
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            new_id = self.cursor.lastrowid
        except:
            self.conn.rollback()

        return new_id

    def execute_stmt(self, sql):
        '''
        Executes statement
        Returns no results

        :param sql: SQL statement
        '''
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            self.conn.rollback()
