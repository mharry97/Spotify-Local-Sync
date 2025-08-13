from thefuzz import fuzz
from itertools import product
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3

from src.database import initialise_database, get_potential_fuzzy_matches

min_score_threshold = 250


# string1 = "USB (Volume 1)"
# string2 = "USB - Volume 1"
#
# # --- Different types of matching ---
#
# # Simple Ratio (less effective for this case)
# simple_score = fuzz.ratio(string1, string2)
# print(f"Simple Ratio Score: {simple_score}")
#
# # Token Set Ratio (the best choice here)
# token_set_score = fuzz.token_set_ratio(string1, string2)
# print(f"Token Set Ratio Score: {token_set_score}")




# Update a local track's metadata with the info from a Spotify track
def update_local_track(local_info, spotify_info):
  con, cur = initialise_database()

  # Find file type from db
  if local_info[4] == ".mp3":
    audio = MP3(local_info[5], ID3=EasyID3)
  elif local_info[4] == ".flac":
    audio = FLAC(local_info[5])
  else:
    print(f"No file type stored for track {local_info[5]}")

  # Overwrite info with spotify data
  audio["title"] = spotify_info[3]
  audio["artist"] = spotify_info[1]
  audio["album"] = spotify_info[2]
  audio.save()

  # Form tuple with new information
  updated_track_tuple = (
    local_info[0],
    spotify_info[0],
    spotify_info[3],
    spotify_info[2],
    spotify_info[1],
    local_info[4],
    local_info[5]
  )

  cur.execute("""
                INSERT INTO local_tracks (audio_hash, gen_id, name, album_name, artist, file_type, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(audio_hash) DO UPDATE SET
                    name = excluded.name,
                    album_name = excluded.album_name,
                    artist = excluded.artist,
                    gen_id = excluded.gen_id
            """, updated_track_tuple)
  con.commit()
  con.close()
  print(f"Updated {local_info[5]}.")


# Expected data shapes
# loc = ("467382496789023324", audio_hash
#         "Luude & Mattafix", artist
#         "Big City Life - Single", album
#         "Big City Life", song
#         ".mp3", file_type
#         "/Users/harry.moore/Documents/jellyfin_media/01 Big City Life.mp3" file_path
#         )
# spot = ("7182392199364454162", gen_id
#        "Luude", artist
#        "Big City Life", album
#        "Big City Life" song
#        )

# Calculate each fuzz score between two songs using song, album and artist name
def get_fuzz_score(local, spot):
  artist_ratio = fuzz.token_set_ratio(local[1], spot[1])
  album_ratio = fuzz.token_set_ratio(local[2], spot[2])
  song_ratio = fuzz.token_set_ratio(local[3], spot[3])

  overall_score = 1.5*artist_ratio + album_ratio + 1.5*song_ratio # Rank artist and song name higher than album

  return overall_score


def find_all_potential_matches():
  print("Retrieving unmatched songs...")
  # Get required data
  unmatched_songs, spotify_songs = get_potential_fuzzy_matches()

  # Compare each unmatched song to each spotify song
  for local_song in unmatched_songs:
    print("Searching for the best match...")
    best_spotify_match = None
    highest_score = 0

    # Search spotify songs for best match
    for spotify_song in spotify_songs:
      current_score = get_fuzz_score(local_song, spotify_song)
      if current_score > highest_score:
        highest_score = current_score
        best_spotify_match = spotify_song

    if highest_score >= min_score_threshold:
      print("\n" + "="*50)
      print("Match Found! Would you like to update with the following changes for Spotify?")
      print("----------INFO----------")
      print(f"File: {local_song[5]}")
      print(f"Score: {highest_score}")
      print("----------Changes----------")
      print(f"Artist: {local_song[1]} -> {best_spotify_match[1]}")
      print(f"Album: {local_song[2]} -> {best_spotify_match[2]}")
      print(f"Song: {local_song[3]} -> {best_spotify_match[3]}")

      while True:
        choice = input("Update metadata with Spotify match? (y/n/s) [yes/no/stop]: ").lower()
        if choice in ['y', 'yes']:
          # User confirmed, update the metadata
          update_local_track(local_song, best_spotify_match)
          break
        elif choice in ['n', 'no']:
          # User skipped, move to the next unmatched song
          print("Skipping...")
          break
        elif choice in ['s', 'stop']:
          # User wants to stop the whole process
          print("Stopping script.")
          return
        else:
          print("Invalid input. Please enter 'y', 'n', or 's'.")


