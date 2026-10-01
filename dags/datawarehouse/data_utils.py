
from airflow.providers.postgres.hooks.postgres import PostgresHook
from pyscopg2.extras import  RealDictCursor

table ="yt_api"

def get_conn_cursor():
    """
    Establishes a connection to the PostgreSQL database and returns a cursor object.

    Returns:
        cursor (RealDictCursor): A cursor object for executing SQL queries.
    """
    # Create a PostgresHook instance
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_etl", database="etl_db")

    # Get a connection from the hook
    conn = hook.get_conn()

    # Create a cursor with RealDictCursor to return results as dictionaries
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    return conn, cursor

def close_conn_cursor(conn, cursor):
    
    cursor.close()  # Close the cursor to avoid resource leaks  
    conn.close()  # Close the connection to avoid resource leaks    

def create_schema(schema):
    """
    Creates a schema in the PostgreSQL database if it does not already exist.

    Args:
        schema (str): The name of the schema to create.
    """
    conn, cursor = get_conn_cursor()
    try:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        conn.commit()  # Commit the transaction to save changes
    except Exception as e:
        print(f"Error creating schema {schema}: {e}")
        conn.rollback()  # Rollback in case of error
    finally:
        close_conn_cursor(conn, cursor)
def create_table(schema, table):
    """
    Creates a table in the specified schema if it does not already exist.

    Args:
        schema (str): The name of the schema where the table will be created.
        table (str): The name of the table to create.
    """
    conn, cursor = get_conn_cursor()
    if schema == "staging":
        table_sql = f"""CREATE TABLE IF NOT EXISTS {schema}.{table} (
        "Video_ID" VARCHAR(255) PRIMARY KEY,
        "Video_Title" TEXT NOT NULL,
        "Upload_Date" TIMESTAMP NOT NULL,
        "Video_Views" INT,
        "Likes_Count" INT,
        "Comments_Count" INT        
        );
    """ 
    else: 
        table_sql = f"""CREATE TABLE IF NOT EXISTS {schema}.{table} (
               "Video_ID" VARCHAR(255) PRIMARY KEY,
               "Video_Title" TEXT NOT NULL,
               "Upload_Date" TIMESTAMP NOT NULL,
               "Duration" TIME NOT NULL,
               "Video_Type" VARCHAR(10) NOT NULL,"
               "Video_Views" INT,
               "Likes_Count" INT,
               "Comments_Count" INT        
               );
        """
        try:
            cursor.execute(table_sql)
            conn.commit()  # Commit the transaction to save changes
        except Exception as e:
            print(f"Error creating table {schema}.{table}: {e}")
            conn.rollback()  # Rollback in case of error
        finally:
            close_conn_cursor(conn, cursor)


def get_video_ids(schema, table):
    """
    Retrieves all video IDs from the specified table in the given schema.

    Args:
        schema (str): The name of the schema where the table is located.
        table (str): The name of the table from which to retrieve video IDs.

    Returns:
        list: A list of video IDs retrieved from the table.
    """
    conn, cursor = get_conn_cursor()
    try:
        cursor.execute(f"SELECT \"Video_ID\" FROM {schema}.{table};")
        video_ids = [row["Video_ID"] for row in cursor.fetchall()]
        return video_ids
    except Exception as e:
        print(f"Error retrieving video IDs from {schema}.{table}: {e}")
        return []
    finally:
        close_conn_cursor(conn, cursor)