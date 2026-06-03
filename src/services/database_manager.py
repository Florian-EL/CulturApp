from pathlib import Path
import sqlite3

from dataclasses import asdict, fields, is_dataclass

from src.models.film import Film
from src.models.serie_film import SerieFilm
from src.models.serie import Serie
from src.models.roman import Roman
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
            MediaType.SERIEFILM: {
                "table": "serie_film",
                "class": SerieFilm
            },
            MediaType.SERIE: {
                "table": "serie",
                "class": Serie
            },
            MediaType.ROMAN: {
                "table": "roman",
                "class": Roman
            },
        }
        self.TYPE_MAP = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "INTEGER",
        }
        
        for config in self.TABLE_MAPPING.values():
            self.sync_table(config["table"], config["class"])
    
    def close(self):
        self.conn.close()
    
    def sync_table(self, table_name, model_cls):
        cursor = self.conn.cursor()
        columns = {}
        
        for f in fields(model_cls):
            py_type = f.type
            sql_type = self.TYPE_MAP.get(py_type, "TEXT")
            columns[f.name] = sql_type
            
        create_sql = ", ".join(
            f"{name} {sql_type}"
            for name, sql_type in columns.items()
        )
        
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} ({create_sql})"
        )
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing = {row[1] for row in cursor.fetchall()}
        
        for col_name, col_type in columns.items():
            if col_name not in existing:
                cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                )
                
        self.conn.commit()
    
    def model_to_row(self, obj):
        if not is_dataclass(obj):
            raise ValueError("Object must be a dataclass")
        
        data = asdict(obj)
        
        if data.get("id") is None:
            data.pop("id", None)
            
        return data
    
    def row_to_model(self, model_cls, row):
        return model_cls(**row)
    
    def add(self, table: str, obj):
        cursor = self.conn.cursor()
        
        data = self.model_to_row(obj)
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(sql, tuple(data.values()))
        self.conn.commit()
        
        obj.id = cursor.lastrowid
    
    def get(self, table: str, model_cls):
        cursor = self.conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table} ORDER BY titre")
        rows = cursor.fetchall()
        
        return [self.row_to_model(model_cls, dict(row)) for row in rows]
        