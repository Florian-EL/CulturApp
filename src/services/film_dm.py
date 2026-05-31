from src.models.film import Film
from src.services.database_manager import DatabaseManager
from src.utils import MediaType


class FilmdataManager:
    def __init__(self):
        self.db = DatabaseManager("./data")
    
    def add_film(self, film: Film):
        self.db.add_movie(film)
    
    def get_films(self):
        return self.db.get_all_movies()
    
