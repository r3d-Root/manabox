import requests

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3/files"


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def find_folder(access_token: str, folder_name: str):
    params = {
        "q": (
            f"name = '{folder_name}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        ),
        "fields": "files(id, name)",
        "pageSize": 10,
    }
    response = requests.get(
        DRIVE_API_BASE,
        headers=_headers(access_token),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    files = response.json().get("files", [])
    return files[0] if files else None


def find_file_in_folder(access_token: str, folder_id: str, filename: str):
    params = {
        "q": (
            f"name = '{filename}' and "
            f"'{folder_id}' in parents and "
            f"trashed = false"
        ),
        "fields": "files(id, name)",
        "pageSize": 10,
    }
    response = requests.get(
        DRIVE_API_BASE,
        headers=_headers(access_token),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    files = response.json().get("files", [])
    return files[0] if files else None


def download_file_bytes(access_token: str, file_id: str) -> bytes:
    response = requests.get(
        f"{DRIVE_API_BASE}/{file_id}",
        headers=_headers(access_token),
        params={"alt": "media"},
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def load_manabox_csv(access_token: str) -> bytes:
    folder = find_folder(access_token, "ManaBox Backups")
    if not folder:
        raise FileNotFoundError("Folder 'ManaBox Backups' not found in Google Drive.")

    csv_file = find_file_in_folder(access_token, folder["id"], "ManaBox_Collection.csv")
    if not csv_file:
        raise FileNotFoundError(
            "File 'ManaBox_Collection.csv' not found inside 'ManaBox Backups'."
        )

    return download_file_bytes(access_token, csv_file["id"])