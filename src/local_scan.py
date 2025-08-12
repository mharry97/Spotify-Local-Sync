import os
from dotenv import load_dotenv
import hashlib
import pathlib
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3

from src.database import initialise_database
from src.utils import gen_hash


# Generate unique hash from audio of file. Allows persistent id when metadata may change.
def generate_audio_hash(filepath):
  # Use a buffer size of 64k. This is efficient for reading files.
  buf_size = 65536

  sha256 = hashlib.sha256()

  try:
    with open(filepath, 'rb') as f:
      while True:
        data = f.read(buf_size)
        if not data:
          break
        sha256.update(data)
    return sha256.hexdigest()
  except IOError:
    # Return None if the file can't be read for some reason
    return None

# Get metadata for a locally stored track
def get_local_track_info(file_path):
  # Parse file path for suffix
  file_type = pathlib.Path(file_path).suffix
  if file_type == ".mp3":
    audio = MP3(file_path, ID3=EasyID3)
  elif file_type == ".flac":
    audio = FLAC(file_path)
  else:
    print(f"Filetype for {file_path} not recognised")
    return None

  artist_list = audio.get('ARTIST')
  artist = artist_list[0] if artist_list else None

  album_list = audio.get('ALBUM')
  album = album_list[0] if album_list else None

  title_list = audio.get('TITLE')
  name = title_list[0] if title_list else None

  audio_hash = generate_audio_hash(file_path)
  gen_id = gen_hash(artist,album,name)


  return artist, gen_id, album, name, audio_hash, file_type


def sync_local():
  load_dotenv()

  # Get an active database connection and cursor
  con, cur = initialise_database()
  supported_extensions = ('.mp3','.flac')

  local_tracks = []
  # Walk through the directory tree
  for root, dirs, files in os.walk(os.getenv("LOCAL_MEDIA_PATH")):
    # Loop through each file found in the current directory
    for file in files:
      if file.startswith('.') or not file.lower().endswith(supported_extensions):
        continue
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
