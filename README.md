# CulturApp

Application de bureau pour organiser une bibliothèque personnelle de contenus culturels : films, séries, romans, mangas, webtoons, histoires Wattpad et citations. L’application est écrite en Python avec PySide6 et stocke les données dans une base SQLite.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Prérequis](#prérequis)
- [Installation et lancement](#installation-et-lancement)
- [Données et configuration](#données-et-configuration)
- [Importer un CSV](#importer-un-csv)
- [Structure du projet](#structure-du-projet)
- [Développement et création d’un exécutable](#développement-et-création-dun-exécutable)
- [Dépannage](#dépannage)

## Fonctionnalités

- Gestion des films, séries, romans, mangas, webtoons et histoires Wattpad, avec leurs métadonnées et leur état d’avancement.
- Gestion des citations associées à une œuvre, un personnage ou un artiste.
- Vue d’accueil et vues par catégorie, tableaux configurables, tri, filtres et formulaires d’ajout, modification et suppression.
- Bibliothèque et galerie d’images associées aux œuvres.
- Import de données CSV depuis l’interface.
- Persistance locale dans SQLite, avec création et mise à jour des tables au démarrage.
- Réglages de l’application, notamment le dossier qui contient les données.

Les champs et valeurs proposés dans les formulaires sont principalement configurés dans `src/assets/config.json`.

## Technologies

- Python 3.13
- PySide6 (interface graphique)
- pandas (lecture et traitement des CSV)
- SQLite (base locale, via `sqlite3` de Python)
- cx_Freeze (construction de l’exécutable Linux)
- watchdog (facultatif, rechargement en développement avec `dev.py`)

## Prérequis

- Python 3.10 ou une version compatible avec les versions installées de PySide6 et pandas.
- `pip` et un environnement virtuel recommandés.
- Un environnement graphique compatible avec Qt pour ouvrir l’application.

Le dépôt ne contient pas de fichier `requirements.txt`. Installez les dépendances nécessaires manuellement :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PySide6 pandas
```

Pour le rechargement automatique ou la construction de l’exécutable, installez aussi les outils correspondants :

```bash
python -m pip install watchdog cx_Freeze
```

## Installation et lancement

Depuis la racine du dépôt :

```bash
python main.py
```

Pour lancer avec surveillance et redémarrage automatique après modification d’un fichier Python :

```bash
python dev.py
```

Arrêtez ce mode avec `Ctrl+C`.

## Données et configuration

`src/assets/config.json` définit les colonnes, les colonnes masquées, les règles de tri initiales, les choix de champs et le dossier de données. Dans la configuration fournie, le dossier est défini sur `/home/florian/Documents/Data/CulturApp/`. Ce chemin est propre à une machine : adaptez-le dans le fichier JSON ou choisissez un autre dossier dans les paramètres de l’application.

Au premier lancement, l’application crée le dossier de données et la base `library.db` si nécessaire. Les tables correspondent aux différents types de contenus. Le dépôt contient également une base et des fichiers CSV dans `data/`, mais la configuration par défaut ne pointe pas nécessairement vers ce dossier. Faites une copie de sauvegarde avant de déplacer ou remplacer une base existante.

`src/assets/config_test.json` est utilisé lorsque l’application est instanciée en mode test. Le lanceur normal `main.py` démarre en mode standard.

## Importer un CSV

Le bouton **Importer CSV** de l’interface ouvre un sélecteur de fichier. La structure attendue dépend de la catégorie affichée et des noms de colonnes configurés dans `src/assets/config.json`. Les exemples de données du dépôt sont dans `data/`. Vérifiez les en-têtes et le séparateur du fichier avant l’import ; le code lit les fichiers CSV avec pandas.

## Structure du projet

```text
CulturApp/
├── main.py                    # Point d’entrée de l’application
├── dev.py                     # Lanceur de développement avec rechargement
├── build.py                   # Configuration cx_Freeze
├── build_linux.sh             # Construction et raccourci Linux
├── data/                      # Base et fichiers de données d’exemple
└── src/
    ├── assets/                # Icône et configurations JSON
    ├── models/                # Modèles des contenus et citations
    ├── services/              # Configuration et accès SQLite
    └── view/                  # Fenêtres, tableaux, formulaires et galerie
```

## Développement et création d’un exécutable

La configuration de cx_Freeze se trouve dans `build.py`. Pour produire un exécutable à partir de la racine :

```bash
python build.py build
```

Le script `build_linux.sh` automatise la construction et l’installation d’un raccourci `.desktop` dans l’espace utilisateur. Il contient des chemins absolus propres à l’environnement d’origine : vérifiez `PROJECT_DIR` et les chemins de sortie avant de l’utiliser sur une autre machine. Ce script modifie le menu des applications de l’utilisateur.

## Dépannage

- **L’application ne trouve pas les données** : vérifiez `data_folder` dans `src/assets/config.json` et les permissions du dossier.
- **La bibliothèque semble vide** : vérifiez que le dossier sélectionné contient la base `library.db` attendue ; la base fournie dans `data/` est distincte du chemin configuré par défaut.
- **Erreur d’import Qt** : activez l’environnement virtuel puis installez PySide6 avec le même interpréteur Python que celui utilisé pour lancer `main.py`.
- **Import CSV incorrect** : vérifiez la catégorie active, les en-têtes et le séparateur du fichier.
