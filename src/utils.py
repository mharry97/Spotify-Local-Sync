import pathlib

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
import hashlib

# Generate normalised hash from track information
def gen_hash(artist, album, song):
  if artist and album and song:
    conc = artist + album + song
    key = conc.lower()
    return hash(key)
  else:
    return None

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


def get_local_track_info(file_path):
  # Parse file path for suffix
  file_type = pathlib.Path(file_path).suffix
  if file_type == ".mp3":
    audio = MP3(file_path)
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
