from flask import Blueprint, url_for, redirect, session, flash
from app.extensions import oauth
from app.services.drive import load_manabox_csv
from app.services.importer import import_collection_csv

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.record_once
def setup_google(state):
    app = state.app
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile https://www.googleapis.com/auth/drive.readonly"
        },
    )

@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(
        redirect_uri,
        prompt="consent",
        access_type="offline",
        )

@auth_bp.route("/callback")
def callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.google.parse_id_token(token)

    session["user"] = {
        "name": userinfo.get("name"),
        "email": userinfo.get("email"),
        "picture": userinfo.get("picture"),
    }
    session["google_token"] = token

    try:
        csv_bytes = load_manabox_csv(token["access_token"])
        import_collection_csv(csv_bytes)
        flash("Loaded ManaBox_Collection.csv from Google Drive.", "success")
    except Exception as exc:
        flash(f"Could not load collection: {exc}", "danger")

    return redirect(url_for("web.index"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.index"))