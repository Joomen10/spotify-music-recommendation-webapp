import os

from flask import Flask, session, request, redirect, url_for

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)  # Set a random secret key for session management

client_id="b1d1a53c290c4c4b9dc855b81887dd74"
client_secret="344a4d6c0da84a0ea109df5b952133ee"
redirect_uri = "http://localhost:5000/callback" 
scope = 'playlist-read-private'  # Replace with the desired scope

# Set up Spotipy OAuth object
cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True,
)

# Create the Spotify client using this auth manager
sp = Spotify(auth_manager=sp_oauth)

@app.route("/")
def home():
    """
    Check if we have a valid token. If not, redirect to Spotify's authorization URL.
    """
    token_info = sp_oauth.validate_token(cache_handler.get_cached_token())
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for("get_playlists"))


@app.route("/callback")
def callback():
    """
    After Spotify's OAuth flow, the user is redirected here with a 'code' in the URL.
    Exchange the code for an access token and store it using FlaskSessionCacheHandler.
    """
    code = request.args.get("code")
    if code:
        sp_oauth.get_access_token(code)  # This auto-saves to the session via cache_handler
    return redirect(url_for("get_playlists"))


@app.route("/get_playlists")
def get_playlists():
    """
    Example route to display the user's playlists. If the token is invalid or expired,
    re-authenticate the user.
    """
    token_info = sp_oauth.validate_token(cache_handler.get_cached_token())
    if not token_info:
        return redirect(sp_oauth.get_authorize_url())

    try:
        playlists = sp.current_user_playlists(limit=10)
    except Exception as e:
        print("Error fetching playlists:", e)
        return f"Error: {e}"

    # Build a simple HTML string of playlist names and URLs
    playlist_info = [(pl["name"], pl["external_urls"]["spotify"]) for pl in playlists["items"]]
    playlist_html = "<br>".join([f"{name}: {url}" for name, url in playlist_info])

    return f"<h3>Your Playlists:</h3><p>{playlist_html}</p>"


@app.route("/logout")
def logout():
    """
    Clear the session and token, forcing a new login on the next request.
    """
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
