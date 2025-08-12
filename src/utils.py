# Generate normalised hash from track information
def gen_hash(artist, album, song):
  if artist and album and song:
    conc = artist + album + song
    key = conc.lower()
    return hash(key)
  else:
    return None
