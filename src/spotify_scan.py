import spotipy
import os
import time
import sys
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from src.database import initialise_database
from src.utils import gen_hash

def sync_spotify():
  # Load environment variables
  load_dotenv()
  client_id = os.getenv("SPOTIFY_CLIENT_ID")
  client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
  redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")



  # Get an active database connection and cursor
  con, cur = initialise_database()

  # Authenticate with spotify
  sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                 client_secret=client_secret,
                                                 redirect_uri=redirect_uri,
                                                 scope="user-library-read"))

  results = sp.current_user_saved_tracks(limit=50)
  num_dots = 0

  # Loop while there are more pages of results
  while results:
    num_dots = (num_dots % 3) + 1
    dots = "." * num_dots
    # The \r moves the cursor to the start of the line to overwrite it
    sys.stdout.write(f"\rFetching saved Spotify songs{dots} ")
    sys.stdout.flush()
    # Create a list of tuples for the current page
    page_tracks = []
    for item in results['items']:
      track = item['track']
      artist_list = [artist['name'] for artist in track['artists']]
      artists_string = ", ".join(artist_list)

      gen_id = gen_hash(track['artists'][0]['name'], track['album']['name'], track['name'])

      song_tuple = (
        gen_id,
        track['id'],
        track['name'],
        track['album']['id'],
        track['album']['name'],
        track['artists'][0]['name'],
        artists_string
      )
      # Add song to page track list
      page_tracks.append(song_tuple)

    # Upsert page tracks to table
    if page_tracks:
      cur.executemany("""
                INSERT INTO spotify_tracks (gen_id, spotify_id, name, album_id, album_name, first_artist, artists)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(spotify_id) DO UPDATE SET
                    name = excluded.name,
                    album_name = excluded.album_name,
                    artists = excluded.artists,
                    first_artist = excluded.first_artist,
                    gen_id = excluded.gen_id
            """, page_tracks)
      con.commit()

    # Get the next page of results
    results = sp.next(results) if results['next'] else None

  print("\nFinished fetching and saving all spotify tracks.")
  con.close()
