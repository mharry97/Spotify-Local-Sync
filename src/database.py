import os
import sqlite3

def initialise_database():
  script_dir = os.path.dirname(os.path.abspath(__file__))
  project_root = os.path.dirname(script_dir)
  db_path = os.path.join(project_root, 'data', 'music_library.db')

  # Create database
  con = sqlite3.connect(db_path)

  # Create cursor
  cur = con.cursor()

  # Create spotify table for storing all saved spotify songs
  cur.execute("""
      CREATE TABLE IF NOT EXISTS spotify_tracks (
          gen_id TEXT,
          spotify_id TEXT PRIMARY KEY,
          name TEXT,
          album_id TEXT,
          album_name TEXT,
          first_artist TEXT,
          artists TEXT
      )
  """)

  # Create local music table
  cur.execute("""
      CREATE TABLE IF NOT EXISTS local_tracks (
          audio_hash TEXT PRIMARY KEY,
          gen_id TEXT,
          name TEXT,
          album_name TEXT,
          artist TEXT,
          file_type TEXT,
          file_path TEXT
      )
  """)

  # Create a view to retrieve info like coverage and songs without info
  cur.execute("DROP VIEW IF EXISTS matched_tracks")
  cur.execute("""
      CREATE VIEW matched_tracks AS
      SELECT
        s.spotify_id,
        s.name AS spotify_name,
        s.first_artist AS spotify_artist,
        s.album_name AS spotify_album,
        COALESCE(l.audio_hash, l1.audio_hash) AS local_audio_hash,
        COALESCE(l.file_path, l1.file_path) AS file_path
      FROM
        spotify_tracks s
      -- Try perfect match on the generated ID
      LEFT JOIN local_tracks l ON s.gen_id = l.gen_id
      -- For anything that didn't match, try matching on artist and song name
      LEFT JOIN local_tracks l1 ON s.first_artist = l1.artist AND s.name = l1.name AND l.audio_hash IS NULL
    """)

  return con, cur

# Get basic coverage stats
def get_coverage_stats():
  con, cur = initialise_database()

  # Query the view to get counts
  cur.execute("""
      SELECT
          COUNT(spotify_id) AS total_spotify_songs,
          COUNT(local_audio_hash) AS matched_songs
      FROM
          matched_tracks
  """)

  # Fetch the single result row
  stats = cur.fetchone()
  con.close()

  if stats and stats[0] > 0:
    total = stats[0]
    matched = stats[1]
    coverage_percent = (matched / total) * 100
    return {
      "total": total,
      "matched": matched,
      "unmatched": total - matched,
      "coverage": round(coverage_percent, 2)
    }
  return None

# Get songs with no matches and all spotify songs for fuzzy matching
def get_potential_fuzzy_matches():
  con, cur = initialise_database()

  # Fetch all mismatches
  cur.execute("""
        SELECT
          l.audio_hash,
          l.artist,
          l.album_name,
          l.name,
          l.file_type,
          l.file_path
        FROM
          local_tracks l
        LEFT JOIN spotify_tracks s ON l.gen_id = s.gen_id
        WHERE  s.gen_id IS NULL
        ORDER BY l.artist ASC
      """)

  unmatched_songs = cur.fetchall()

  # Fetch all spotify songs
  cur.execute("""
          SELECT
            s.gen_id,
            s.first_artist,
            s.album_name,
            s.name
          FROM
            spotify_tracks s
        """)

  spotify_songs = cur.fetchall()

  con.close()

  return unmatched_songs, spotify_songs

# Get data for specific local song
def get_local_song(audio_hash):
  con, cur = initialise_database()

  cur.execute("""
    SELECT
      l.audio_hash,
      l.artist,
      l.album_name,
      l.name,
      l.file_type,
      l.file_path
    FROM
      local_tracks l
    WHERE
      audio_hash = ?
  """, (audio_hash, ))

  song_data = cur.fetchone()
  con.close()
  return song_data



# Remove a song
def delete_song(song):
  con, cur = initialise_database()

  # Fetch all mismatches
  cur.execute("""
  DELETE FROM local_tracks WHERE name = "?"
  """,song)
  con.commit()
  con.close()
