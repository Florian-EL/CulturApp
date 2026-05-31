import json
from pathlib import Path
import sys


class ConfigManager:
    """Gère la configuration de l'application (chemin du dossier data, etc.)"""
    
    def __init__(self):
        # Déterminer le répertoire de base de l'application
        self.app_dir = self._get_app_dir()
        
        # Chemin du fichier config : à côté de l'exécutable
        self.config_file = self.app_dir / "src/assets/config.json"
        self.default_data_folder = self.app_dir / "data"
        
        self.config = self._load_config()
    
    def _get_app_dir(self):
        """
        Retourne le répertoire de base de l'application
        - En mode développement : répertoire du projet
        - En mode build (cx_Freeze) : répertoire contenant l'exécutable
        """
        # Pour cx_Freeze ou exécutable standalone
        if getattr(sys, 'frozen', False):
            # Mode frozen (cx_Freeze)
            return Path(sys.executable).parent
        else:
            # Mode développement : parent du dossier src
            current_file = Path(__file__).resolve()
            # src/services/config_manager.py -> root
            return current_file.parent.parent.parent
    
    def _load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self):
        """Retourne la configuration par défaut"""
        return {
            "data_folder": str(self.default_data_folder)
        }
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_data_folder(self) -> Path:
        """Retourne le chemin du dossier data"""
        folder = self.config.get("data_folder", str(self.default_data_folder))
        return Path(folder).expanduser().resolve()
    
    def set_data_folder(self, folder_path: str):
        """Change le chemin du dossier data"""
        folder = Path(folder_path).expanduser().resolve()
        self.config["data_folder"] = str(folder)
        self.save_config()
    
    def get_config_file(self) -> Path:
        """Retourne le chemin du fichier de configuration"""
        return self.config_file
