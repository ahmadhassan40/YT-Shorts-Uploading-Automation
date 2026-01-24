import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from core.engine_interface import UploadEngine, VideoMetadata
from config.config_loader import config

logger = logging.getLogger(__name__)

class YouTubeUploadEngine(UploadEngine):
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self):
        self.client_secrets_file = config.get("youtube.client_secrets_file", "config/client_secrets.json")
        self.token_file = config.get("youtube.token_file", "config/token.json")
        self.credentials = None

    def authenticate(self):
        """
        Authenticates the user using OAuth 2.0.
        """
        logger.info("Authenticating with YouTube...")
        if os.path.exists(self.token_file):
            self.credentials = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired token...")
                self.credentials.refresh(Request())
            else:
                logger.info("No valid token found. Initiating new login...")
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(f"Client secrets file not found at {self.client_secrets_file}. Cannot authenticate.")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.credentials.to_json())
                logger.info(f"Token saved to {self.token_file}")

    def upload_video(self, video_path: str, metadata: VideoMetadata) -> str:
        """
        Uploads a video to YouTube.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")

        if not self.credentials:
            self.authenticate()

        youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=self.credentials)

        logger.info(f"Uploading {video_path}...")
        
        body = {
            "snippet": {
                "title": metadata.title,
                "description": metadata.description,
                "tags": metadata.tags,
                "categoryId": "28" # Science & Technology
            },
            "status": {
                "privacyStatus": metadata.privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        # Chunk size: 4MB
        media = MediaFileUpload(video_path, chunksize=4*1024*1024, resumable=True, mimetype="video/mp4")

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"Upload Completed! URL: {video_url}")
        
        return video_url
