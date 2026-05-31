from src.models.film import Film


class FilmdataManager:
    def __init__(self):
        self.data = []
    
    def add_film(self, film: Film):
        self.data.append(film)
    
    def get_films(self):
        return self.data