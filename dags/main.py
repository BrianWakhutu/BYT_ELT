from airflow import DAG
import pendulum
from datetime import datetime,timedelta
from api.video_stats import get_playlist_id, get_video_ids,extract_video_data, save_to_json

# Define local timezone
local_tz = pendulum.timezone("Africa/Nairobi")

# Default arguments for the DAG
default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": ['brian.wakhutu@gmail.com'],
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(minutes=60),
    "start_date": datetime(2025, 1, 1, tzinfo=local_tz)
}
with DAG(
    dag_id="produce_json",
    default_args={
        "owner": "dataengineers",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
    },
    description="A DAG to produce JSON File with raw Data",
    start_date=pendulum.datetime(2025, 1, 1, tz="Africa/Nairobi"),
    schedule="0 14 * * *",
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=60),
) as dag:
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extract_data = extract_video_data(video_ids)
    save_to_json_task = save_to_json(extract_data)
    # Define dependecies

    playlist_id >> video_ids >> extract_data >> save_to_json_task