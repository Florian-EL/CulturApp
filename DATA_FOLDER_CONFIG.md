# Configuration du Dossier Data - Guide Complet

## Vue d'ensemble

L'application utilise maintenant un système de configuration flexible qui permet au code de pointer vers le dossier `data` même après le build, et permet à l'utilisateur de changer ce chemin via l'interface utilisateur.

## Fonctionnement

### 1. **ConfigManager** (`src/services/config_manager.py`)
- Gère un fichier `config.json` qui stocke le chemin du dossier data
- Détecte automatiquement si l'app est en mode développement ou build (cx_Freeze)
- Crée le fichier de config au premier lancement avec les valeurs par défaut

**Mode développement** :
- `app_dir` = répertoire racine du projet
- `config.json` créé à la racine du projet

**Mode build (cx_Freeze)** :
- `app_dir` = répertoire contenant l'exécutable
- `config.json` créé à côté de l'exécutable

### 2. **Settings Dialog** (`src/view/settings_dialog.py`)
- Interface pour permettre à l'utilisateur de changer le dossier data
- Un bouton "Paramètres" en bas du menu latéral
- Dialogue avec :
  - Affichage du chemin actuel du dossier data
  - Bouton "Parcourir..." pour sélectionner un nouveau dossier
  - Boutons "Enregistrer" et "Annuler"

### 3. **Modifications du code**
- `main.py` : Initialise ConfigManager et récupère le chemin du data folder
- `main_window.py` : Reçoit le chemin et le passe à FilmWidget
- `film_tab.py` : Reçoit le chemin et le passe à FilmdataManager
- `build.py` : Inclut le dossier `data` dans le build

## Utilisation

### En mode développement

L'application cherche automatiquement le dossier `data` à la racine du projet.

1. Lancez l'app :
```bash
python main.py
```

2. Un fichier `config.json` est créé à la racine avec :
```json
{
    "data_folder": "/chemin/complet/vers/CulturApp/data"
}
```

3. Cliquez sur "Paramètres" pour changer le dossier

### Après build avec cx_Freeze

1. Rebuilder l'app :
```bash
python build.py build
```

2. L'exécutable se trouve dans `build/exe.linux-x86_64-3.13/CulturApp`

3. Les fichiers de données sont inclus : `build/exe.linux-x86_64-3.13/data/`

4. Un `config.json` est créé au même niveau que l'exécutable

5. L'utilisateur peut changer le dossier data via le menu Paramètres

## Chemins gérés

### Chemin par défaut (dans config.json)
- **Dev** : `/home/florian/Documents/Projets/Algo/CulturApp/data`
- **Build** : `./data` (relative à l'exécutable)

### Chemin personnalisé
L'utilisateur peut spécifier n'importe quel chemin absolu ou relatif via le dialogue Paramètres.

## Structure des fichiers

```
CulturApp/
├── main.py              # Initialise ConfigManager
├── build.py             # Inclut data dans le build
├── config.json          # Créé au premier lancement
├── data/                # Dossier des données
│   └── library.db       # Base de données
├── src/
│   ├── services/
│   │   ├── config_manager.py      # NOUVEAU: Gère la configuration
│   │   ├── film_dm.py             # Reçoit le chemin data
│   │   └── database_manager.py    # Crée la BDD au chemin spécifié
│   └── view/
│       ├── main_window.py         # Modifié: passe data_folder
│       ├── film_tab.py            # Modifié: reçoit data_folder
│       └── settings_dialog.py     # NOUVEAU: Interface de paramètres
```

## Avantages

✅ **Portable** : L'app fonctionne peu importe où on la lance  
✅ **Flexible** : L'utilisateur peut changer le dossier des données  
✅ **Persistent** : Les paramètres sont sauvegardés dans config.json  
✅ **Compatible build** : Fonctionne en mode dev et en mode build cx_Freeze  
✅ **Chemins absolus** : Évite les problèmes de chemins relatifs après build  

## Notes importantes

1. **Redémarrage requis** : Les changements de dossier data prennent effet au redémarrage de l'app
2. **Permissions** : L'utilisateur doit avoir les permissions de lecture/écriture sur le dossier data sélectionné
3. **Sauvegarde** : Le fichier `config.json` est sauvegardé automatiquement dans le même répertoire que l'exécutable (ou la racine du projet en dev)
