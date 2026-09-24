import requests
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = "MrBeast"
maxResults = 50



def get_playlist_id():
    try:
            url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}"

            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            json_data = json.dumps(data, indent=4)

            # print(json_data)
            channel_items = data['items'][0]
            channel_playlist_id = channel_items['contentDetails']['relatedPlaylists']['uploads']
            print(channel_playlist_id)
            return channel_playlist_id
    except requests.exceptions.RequestException as e:
         raise e


def get_video_ids(playlist_id):

    video_ids = []
    page_token = None

    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlist_id}&key={API_KEY}"

    try:
        while True:
            url = base_url
            if page_token:
                url += f"&pageToken={page_token}"

            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            # json_data = json.dumps(data, indent=4)

            # print(json_data)
          
            for item in data.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)

            page_token = data.get('nextPageToken')
            if not page_token:
                break

        return video_ids
         
    except requests.exceptions.RequestException as e:
        raise e

        

def extract_video_data(video_ids):
    extracted_data = []

    def batch_list(video_id_lst,batch_size):
        for i in range(0, len(video_id_lst), batch_size):
           yield video_id_lst[i:i + batch_size]

   

    try: 
        for batch in batch_list(video_ids, maxResults):
            video_ids_str = ",".join(batch)
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={API_KEY}"

            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            for item in data.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                contentDetails = item['contentDetails']
                statistics = item['statistics']

                video_data = {
                    "video_id": video_id,
                    "title": snippet['title'],
                    "publishedAt": snippet['publishedAt'],
                    "duration": contentDetails['duration'],
                    "viewCount": statistics.get('viewCount', None),
                    "likeCount": statistics.get('likeCount', None),
                    "commentCount": statistics.get('commentCount', None)
                   
                }
                extracted_data.append(video_data)

            return extracted_data

    except requests.exceptions.RequestException as e:
        raise e

if __name__ == "__main__":
      playlist_id = get_playlist_id()
      video_ids = get_video_ids(playlist_id)
      extract_video_data(video_ids)
