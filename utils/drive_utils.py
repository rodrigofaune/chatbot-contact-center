from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    return service


def list_files_in_folder(folder_id):
    service = get_drive_service()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        pageSize=100,
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])
    return items


def list_files_in_folder_recursive(folder_id):
    service = get_drive_service()
    all_files = []
    
    def _list_files(folder_id, path="/"):
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            pageSize=1000,
            fields="files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                print(f"[Carpeta] {path}{item['name']}/ (ID: {item['id']})")
                _list_files(item['id'], path + item['name'] + "/")
            else:
                print(f"[Archivo] {path}{item['name']} (ID: {item['id']}, Tipo: {item['mimeType']})")
                all_files.append(item)
    _list_files(folder_id)
    return all_files

# Ejemplo de uso:
# folder_id = '1KQWKE69WbSDgmDuosbIJNON_hfBN0aq6'
# files = list_files_in_folder(folder_id)
# for f in files:
#     print(f["name"], f["id"], f["mimeType"]) 