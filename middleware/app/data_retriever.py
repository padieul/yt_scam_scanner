import os
import httplib2
import googleapiclient
import googleapiclient.discovery
from oauth2client import client, GOOGLE_TOKEN_URI

from elasticsearch import helpers
from elasticsearch import Elasticsearch


CLIENT_ID = "737324637694-b6ngjvspqdgv9cbkto3li52ljcl09k4h.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REFRESH_TOKEN = "refresh_token"
DEVELOPER_KEY = "AIzaSyB3pX9aY3rmP8xZSngxxX14NseZ6KCxb0U"


class YtDataRetriever:

    def __init__(self):
        self._data_response = {}

        credentials = client.OAuth2Credentials(
            access_token=None,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            refresh_token=REFRESH_TOKEN,
            token_expiry=None,
            token_uri=GOOGLE_TOKEN_URI,
            user_agent=None,
            revoke_uri=None)

        self.http = credentials.authorize(httplib2.Http())


    def get_video_data(self, video_id: str):

        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.

        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = 'client_secret_737324637694-2c43sarhojqelig5rhvmp4pgkh8oiv5c.apps.googleusercontent.com.json'

        api_service_name = "youtube"
        api_version = "v3"

        youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

        request = youtube.commentThreads().list(
            part="id, replies, snippet",
            videoId=video_id,
            maxResults= 500)

        self._data_response = request.execute()
        return self._data_response


class ESConnect:

    def __init__(self):
        #self._es_client = Elasticsearch("http://es01:9200", auth=("elastic", "1234"))
        self._es_client = Elasticsearch("http://localhost:9200")
        self._es_index = "yt_video"
        self._es_index_name = ""


    def store_video_data(self, video_comments_data, video_id):
        comments = []
        for item in video_comments_data["items"]:
            text_original = item['snippet']['topLevelComment']['snippet']['textOriginal']
            text_original = text_original.replace("\n", "")
            comments.append(text_original)

        actions = []
        self._es_index_name = str(self._es_index) + "_" + str(video_id)

        for i, line in enumerate(comments):
            source = {'content' : line}

            print(self._es_index_name)
            action = {
                        "_index": self._es_index_name.lower(),
                        '_op_type': 'index',
                        "_type": '_doc',
                        "_id": i,
                        "_source": source
                    }
            actions.append(action)

        helpers.bulk(self._es_client, actions)


if __name__ == "__main__":
    yt = YtDataRetriever()
    es = ESConnect()
    VIDEO_ID = "kdcvyfjuKCw"
    data = yt.get_video_data(VIDEO_ID)
    print(data)
    es.store_video_data(data, VIDEO_ID)
