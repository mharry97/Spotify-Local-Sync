import os
from dotenv import load_dotenv

from src.database import initialise_database
from src.utils import get_local_track_info


def sync_local():
  load_dotenv()

  # Get an active database connection and cursor
  con, cur = initialise_database()

  local_tracks = []
  # Walk through the directory tree
  for root, dirs, files in os.walk(os.getenv("LOCAL_MEDIA_PATH")):
    # Loop through each file found in the current directory
    for file in files:
      # Create full path
      full_path = os.path.join(root, file)

      # Get the tags for the single file
      (artist, gen_id, album, name, audio_hash, file_type) = get_local_track_info(full_path)
      song_tuple = (
        audio_hash,
        gen_id,
        name,
        album,
        artist,
        file_type,
        full_path
      )
      # Add to local tracks
      local_tracks.append(song_tuple)

  # Upsert page tracks to table
  if local_tracks:
    cur.executemany("""
              INSERT INTO local_tracks (audio_hash, gen_id, name, album_name, artist, file_type, file_path)
              VALUES (?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(audio_hash) DO UPDATE SET
                  name = excluded.name,
                  album_name = excluded.album_name,
                  artist = excluded.artist,
                  gen_id = excluded.gen_id,
                  file_type = excluded.file_type,
                  file_path = excluded.file_path
          """, local_tracks)
    con.commit()
    print(f"Upserted {len(local_tracks)} tracks.")
  con.close()
