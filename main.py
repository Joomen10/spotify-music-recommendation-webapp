import os
import urllib.parse
import requests


from datetime import datetime, timedelta
from flask import Flask, session, request, redirect, jsonify

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler


app = Flask(__name__)
app.secret_key = '53dalfjaf-adflkja-123124123-123124'
# app.config["SECRET_KEY"] = os.urandom(24)  # Set a random secret key for session management

CLIENT_ID="b1d1a53c290c4c4b9dc855b81887dd74"
CLIENT_SECRET="344a4d6c0da84a0ea109df5b952133ee"
REDIRECT_URI = "http://localhost:5000/callback" 

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

API_BASE_URL = "https://api.spotify.com/v1/"

@app.route("/")
def index():
    return "Welcome to the Spotify API Flask App! <br> <a href='/login'>Login with Spotify</a>"

@app.route("/login")
def login():

    scope = 'user-read-private user-read-email'  # Replace with the desired scope

    params = {
    'client_id' : CLIENT_ID,
    'response_type' : 'code',
    'scope' : scope,
    'client_secret' : CLIENT_SECRET,
    'redirect_uri' : REDIRECT_URI,
    'show_dialog' : True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route("/callback")
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args["error"]})
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/playlists')

@app.route("/playlists")
def get_playlists():

    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f'Bearer {session['access_token']}'
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return jsonify(playlists)

@app.route("/refresh-token")
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        print("Token expired, refreshing...")
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlists')

# @app.route("/logout")
# def logout():
#     """
#     Clear the session and token, forcing a new login on the next request.
#     """
#     session.clear()
#     return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
