import pandas as pd 
import pymysql

# Define MySQL connection parameters
MySQL_DB_HOST = 'localhost'
MySQL_DB_USER = 'root'
MySQL_DB_PASSWORD = 'zentarus'
MySQL_DB_NAME = 'academicworld'


# Function to fetch data from the MySQL localhost
def mysql_query(query):
    """
    Attempts to return SQL query result as a pandas DataFrame

    Parameters:
    query (str): SQL query string

    Returns:
    pandas.DataFrame: Query result

    Example:
    #>>> MySQL_query("SELECT * FROM professor;")

    Returns:
    pandas.DataFrame with corresponding schema and table data
    """

    connection = pymysql.connect(host=MySQL_DB_HOST, user=MySQL_DB_USER, password=MySQL_DB_PASSWORD,
                                 database=MySQL_DB_NAME, port=3306, autocommit=True)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

            # print("data: ", data) # Debug

            if len(data):
                columns = [col[0] for col in cursor.description]
                df = pd.DataFrame(data, columns=columns)
                return df
            else:
                return pd.DataFrame()
    finally:
        connection.close()