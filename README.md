# ManaBox Collection Viewer

A Flask web app that:

- logs in with Google
- loads `ManaBox_Collection.csv` from your Google Drive
- imports the collection into SQLite
- enriches the collection with Scryfall card data
- displays the collection in a fast, searchable, filterable table
- shows sync progress while building the Scryfall cache

---

## Features

- Google OAuth login
- Google Drive integration
- Automatic import from:
  - folder: `ManaBox Backups`
  - file: `ManaBox_Collection.csv`
- SQLite-backed local cache
- Scryfall batch syncing using the collection endpoint
- Sync progress bar
- Server-side paging, sorting, and filtering
- Card hover preview
- Dark mode UI
- Swagger docs for backend API

---

## Tech Stack

- Flask
- Flask-SQLAlchemy
- Authlib
- flask-smorest
- SQLite
- Bootstrap 5
- DataTables
- Scryfall API
- Google Drive API

---

## Project Structure

```text
manabox-app/
├── app.py
├── config.py
├── requirements.txt
├── .env
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── auth/
│   │   └── routes.py
│   ├── web/
│   │   └── routes.py
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── models/
│   │   ├── collection.py
│   │   ├── scryfall.py
│   │   └── sync_status.py
│   ├── services/
│   │   ├── drive.py
│   │   ├── importer.py
│   │   └── scryfall.py
│   ├── templates/
│   │   ├── base.html
│   │   └── collection.html
│   └── static/
│       └── app.css
└── manabox.db

