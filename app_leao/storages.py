import io
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


class GoogleDriveStorage(Storage):
    def __init__(self, folder_id=None):
        self.folder_id = folder_id or getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        base_dir = getattr(settings, 'BASE_DIR', '')
        self.token_path = os.path.join(str(base_dir), 'token.json')
        self._service = None

    @property
    def service(self):
        if not self._service:
            if not os.path.exists(self.token_path):
                raise FileNotFoundError(f"Arquivo token.json não encontrado em: {self.token_path}")

            scopes = ['https://www.googleapis.com/auth/drive']
            creds = Credentials.from_authorized_user_file(self.token_path, scopes=scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(self.token_path, 'w', encoding='utf-8') as f:
                        f.write(creds.to_json())
                else:
                    raise ValueError("Credenciais inválidas no token.json")

            self._service = build('drive', 'v3', credentials=creds)
        return self._service

    def upload_file_stream(self, file_obj, filename):
        file_metadata = {'name': filename}
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]

        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

        content_type = getattr(file_obj, 'content_type', 'application/octet-stream')
        media = MediaIoBaseUpload(file_obj, mimetype=content_type, resumable=True)

        drive_file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        ).execute()

        return drive_file.get('id')

    def _save(self, name, content):
        return self.upload_file_stream(content.file if hasattr(content, 'file') else content, name)

    def _open(self, name, mode='rb'):
        request = self.service.files().get_media(fileId=name)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return ContentFile(fh.read(), name=name)

    def delete(self, name):
        try:
            self.service.files().delete(fileId=name).execute()
        except Exception:
            pass

    def exists(self, name):
        return False

    def url(self, name):
        return f"https://drive.google.com/file/d/{name}/view"