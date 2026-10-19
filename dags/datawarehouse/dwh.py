import logging

from airflow.decorators import task

from datawarehouse.data_loading import load_data
from datawarehouse.data_modification import insert_rows, delete_rows
from datawarehouse.data_transformation import transform_data
from datawarehouse.data_utils import (
    get_conn_cursor,
    create_schema,
    create_table,
    get_video_ids,
)

logger = logging.getLogger(__name__)
table = "yt_api"


def close_resources(conn, cursor):
    """Close any database resources that were successfully opened."""
    try:
        if cursor is not None:
            cursor.close()
    finally:
        if conn is not None:
            conn.close()


@task
def staging_table():
    schema = "staging"
    conn, cursor = None, None

    try:
        conn, cursor = get_conn_cursor()

        yt_data = load_data()
        if not yt_data:
            raise ValueError(
                "No YouTube data was loaded; stopping to avoid deleting staging rows."
            )

        create_schema(schema)
        create_table(schema, table)

        # get_video_ids(schema, table) returns a list of video ID strings.
        existing_ids = set(get_video_ids(schema, table))
        json_ids = {row["video_id"] for row in yt_data}

        # insert_rows should insert new rows and update existing rows using ON CONFLICT.
        for row in yt_data:
            insert_rows(cursor, conn, schema, row)

        # Remove staging rows that are no longer present in the JSON file.
        ids_to_delete = existing_ids - json_ids
        if ids_to_delete:
            delete_rows(cursor, conn, schema, ids_to_delete)

        logger.info("Staging table %s.%s updated successfully.", schema, table)

    except Exception:
        logger.exception("Error updating staging table %s.%s", schema, table)
        raise

    finally:
        close_resources(conn, cursor)


@task
def core_table():
    schema = "core"
    conn, cursor = None, None

    try:
        conn, cursor = get_conn_cursor()

        create_schema(schema)
        create_table(schema, table)

        # Get existing core IDs before processing staging rows.
        existing_core_ids = set(get_video_ids(schema, table))

        # Alias PostgreSQL column names to the keys expected by transform_data().
        cursor.execute("""
            SELECT
                "Video_ID" AS video_id,
                "Video_Title" AS title,
                "Upload_Date" AS "publishedAt",
                "Duration" AS duration,
                "Video_Views" AS "viewCount",
                "Likes_Count" AS "likeCount",
                "Comments_Count" AS "commentCount"
            FROM staging.yt_api
        """)
        staging_rows = cursor.fetchall()

        if not staging_rows:
            raise ValueError(
                "The staging table is empty; stopping to avoid deleting core rows."
            )

        staging_ids = {row["video_id"] for row in staging_rows}

        # Transform each staging row, then insert or update it in core.
        for row in staging_rows:
            transformed_row = transform_data(row)
            insert_rows(cursor, conn, schema, transformed_row)

        # Remove core rows that are no longer present in staging.
        ids_to_delete = existing_core_ids - staging_ids
        if ids_to_delete:
            delete_rows(cursor, conn, schema, ids_to_delete)

        logger.info("Core table %s.%s updated successfully.", schema, table)

    except Exception:
        logger.exception("Error updating core table %s.%s", schema, table)
        raise

    finally:
        close_resources(conn, cursor)