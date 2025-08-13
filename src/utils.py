from hashlib import md5

# Generate normalised hash from track information
def gen_hash(artist, album, song):
  if artist and album and song:
    conc = artist + album + song
    key = conc.lower()
    return md5(key.encode()).hexdigest()
  else:
    return None
