# Fluent Profile Generator

Générateur de fichiers `.prof` pour Ansys Fluent avec interface graphique guidée.

## 📋 Description

Application permettant de transformer des fichiers CSV de débits (Q) et températures (T) en fichiers de profil Fluent (`.prof`) avec interpolation et lissage configurables.

## ✨ Fonctionnalités

- **Interface guidée en 4 étapes** : workflow intuitif et progressif
- **Interpolation et lissage** : paramètres séparés pour débits et températures
- **Visualisation interactive** : prévisualisation en temps réel des courbes
- **Navigation flexible** : possibilité de revenir en arrière pour ajuster les paramètres
- **Export optimisé** : génération de fichiers `.prof` au format Fluent
- **Français et anglais** : sélecteur de langue accessible depuis toutes les étapes

## 🚀 Installation

### Prérequis

- Python 3.8+
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## 💻 Utilisation

### Lancement de l'application

**Méthode 1 - Scripts rapides (recommandé)** :
```bash
# Linux/Mac
./run.sh

# Windows
run.bat
```

**Méthode 2 - Script Python** :
```bash
python launch.py
```

**Méthode 3 - Make** :
```bash
make run
```

### Langue

L'application démarre en français. Le sélecteur en haut à droite bascule vers
l'anglais, et inversement, sans perdre le travail en cours : fichier chargé,
mapping, méthodes et zones sont conservés. Le choix est mémorisé pour les
sessions suivantes.

### Workflow

1. **Sélection des fichiers** : Choisir les 4 fichiers CSV (Q_inlet1, T_inlet1, Q_inlet2, T_inlet2)
2. **Paramétrage** : Ajuster le pas de temps et les facteurs de lissage avec prévisualisation
3. **Prévisualisation** : Vérifier les courbes interpolées
4. **Export** : Sauvegarder le fichier `.prof`

### Format des fichiers CSV d'entrée

Chaque fichier doit contenir 2 colonnes :
- Colonne 1 : Temps (en millisecondes)
- Colonne 2 : Valeur (débit ou température)

Séparateurs supportés : tabulation, point-virgule, virgule, espaces

## 🧪 Tests

### Lancer tous les tests

```bash
pytest tests/ -v
```

### Lancer les tests avec couverture

```bash
pytest tests/ --cov=src --cov-report=html
```

### Lancer un module de tests spécifique

```bash
pytest tests/test_io.py -v
```

## 📁 Structure du projet

```
fluent-prof-generator/
├── launch.py                    # Point d'entrée de l'application
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── io.py              # Lecture/écriture de fichiers
│   │   ├── interpolation.py   # Interpolation et lissage
│   │   └── constants.py       # Constantes
│   └── gui/
│       ├── __init__.py
│       ├── app.py             # Application principale
│       └── steps/
│           ├── __init__.py
│           ├── step1_files.py     # Sélection des fichiers
│           ├── step2_params.py    # Paramètres
│           ├── step3_preview.py   # Prévisualisation
│           └── step4_export.py    # Export
├── tests/
│   ├── __init__.py
│   ├── test_io.py
│   ├── test_interpolation.py
│   └── fixtures/               # Fichiers de test
│       ├── test_Q.csv
│       └── test_T.csv
├── requirements.txt
├── setup.py
├── .gitignore
└── README.md
```

## 🔧 Configuration

Les paramètres par défaut peuvent être modifiés dans `src/core/constants.py` :

- `DEFAULT_DT_US` : Pas de temps par défaut (µs)
- `DEFAULT_FLOW_EPS` : Valeur de remplacement pour les débits nuls
- `DEFAULT_SMOOTH_Q` : Facteur de lissage pour les débits
- `DEFAULT_SMOOTH_T` : Facteur de lissage pour les températures

## ❓ Dépannage

### `ImportError: attempted relative import`

Lancez l'application depuis la racine avec `python launch.py` ou `run.bat` / `./run.sh`.

### `ModuleNotFoundError: No module named 'numpy'`

```bash
pip install -r requirements.txt
```

### tkinter non disponible (Linux)

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk
# Fedora
sudo dnf install python3-tkinter
# macOS (Homebrew)
brew install python-tk
```

## 📝 Licence

MIT License

## 👤 Auteur

Romain
