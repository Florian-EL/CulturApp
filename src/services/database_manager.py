from pathlib import Path
import sqlite3

from src.models.film import Film
from src.utils import MediaType


class DatabaseManager:
    def __init__(self, db_folder: str):
        self.db_folder = Path(db_folder)
        self.db_folder.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.db_folder / "library.db"
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.TABLE_MAPPING = {
            MediaType.FILM: {
                "table": "film",
                "class": Film
            },
        }
        
        self.create_tables()
    
    def close(self):
        self.conn.close()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS film(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            note INTEGER
        )
        """)
        
        self.conn.commit()
    
    def add_movie(self, movie: Film):
        cursor = self.conn.cursor()
        
        cursor.execute("""
        INSERT INTO film(
            titre,
            note
        )
        VALUES (?, ?)
        """,
        (
            movie.titre,
            movie.note
        ))
        
        self.conn.commit()
        
        movie.id = cursor.lastrowid
    
    def get_all_movies(self) -> list[Film]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT *
        FROM film
        ORDER BY titre
        """)
        return [Film(
            id       = row["id"],
            titre    = row["titre"],
            note     = row["note"]
            )
            for row in cursor.fetchall()]