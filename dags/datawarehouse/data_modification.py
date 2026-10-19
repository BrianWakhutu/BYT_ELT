import logging

logger = logging.getLogger(__name__)
table = "yt_api"

def insert_rows(cursor, conn, schema, row):
    video_id = row.get("video_id") if schema == "staging" else row.get("Video_ID")

    try:
        if schema == "staging":
            query = f"""
                INSERT INTO {schema}.{table} (
                    "Video_ID", "Video_Title", "Upload_Date", "Duration",
                    "Video_Views", "Likes_Count", "Comments_Count"
                )
                VALUES (
                    %(video_id)s, %(title)s, %(publishedAt)s, %(duration)s,
                    %(viewCount)s, %(likeCount)s, %(commentCount)s
                )
                ON CONFLICT ("Video_ID") DO UPDATE SET
                    "Video_Title" = EXCLUDED."Video_Title",
                    "Upload_Date" = EXCLUDED."Upload_Date",
                    "Duration" = EXCLUDED."Duration",
                    "Video_Views" = EXCLUDED."Video_Views",
                    "Likes_Count" = EXCLUDED."Likes_Count",
                    "Comments_Count" = EXCLUDED."Comments_Count";
            """
        else:
            query = f"""
                INSERT INTO {schema}.{table} (
                    "Video_ID", "Video_Title", "Upload_Date", "Duration",
                    "Video_Type", "Video_Views", "Likes_Count", "Comments_Count"
                )
                VALUES (
                    %(Video_ID)s, %(Video_Title)s, %(Upload_Date)s, %(Duration)s,
                    %(Video_Type)s, %(Video_Views)s, %(Likes_Count)s, %(Comments_Count)s
                )
                ON CONFLICT ("Video_ID") DO UPDATE SET
                    "Video_Title" = EXCLUDED."Video_Title",
                    "Upload_Date" = EXCLUDED."Upload_Date",
                    "Duration" = EXCLUDED."Duration",
                    "Video_Type" = EXCLUDED."Video_Type",
                    "Video_Views" = EXCLUDED."Video_Views",
                    "Likes_Count" = EXCLUDED."Likes_Count",
                    "Comments_Count" = EXCLUDED."Comments_Count";
            """

        cursor.execute(query, row)
        conn.commit()
        logger.info("Inserted or updated %s.%s for Video_ID %s",
                    schema, table, video_id)

    except Exception:
        conn.rollback()
        logger.exception("Insert/update failed for %s.%s, Video_ID %s",
                         schema, table, video_id)
        raise
def update_rows(cursor, conn, schema, row): 
    try: 
        if schema == "staging":
            video_id = 'video_id'
            upload_date = 'publishedAt'
            video_title = 'title'   
            video_views = 'viewCount'   
            likes_count = 'likeCount'
            comments_count = 'commentCount'
        else:
            video_id = 'Video_ID'
            upload_date = 'Upload_Date'
            video_title = 'Video_Title'
            video_views = 'Video_Views'
            likes_count = 'Likes_Count'
            comments_count = 'Comments_Count'
        
        cursor.execute(f"""
                     UPDATE {schema}.{table}
                     SET "Video_Title" = %(video_title)s,
                         "Upload_Date" = %(upload_date)s,
                         "Video_Views" = %(video_views)s,
                         "Likes_Count" = %(likes_count)s,
                         "Comments_Count" = %(comments_count)s
                     WHERE "Video_ID" = %(video_id)s AND "Upload_Date" = %(upload_date)s;
                     """, row
        )
        conn.commit()  # Commit the transaction to save changes
        logger.info(f"Successfully updated row in {schema}.{table}: {row} with Video_ID: {row.get('video_id')}")
    except Exception as e:
        logger.error(f"Error updating row in {schema}.{table}: {e} with Video_ID: {row.get('video_id')}")
        raise  e # Re-raise the exception to propagate it
def delete_rows(cursor, conn, schema, ids_to_delete):
    if not ids_to_delete:
        return

    try:
        cursor.execute(
            f'DELETE FROM {schema}.{table} WHERE "Video_ID" = ANY(%s);',
            (list(ids_to_delete),),
        )
        conn.commit()
        logger.info(
            "Deleted %s rows from %s.%s",
            cursor.rowcount,
            schema,
            table,
        )
    except Exception:
        conn.rollback()
        logger.exception("Error deleting rows from %s.%s", schema, table)
        raise