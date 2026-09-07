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

## 🚀 Installation

**Aucune installation n'est nécessaire.** Copiez le dossier du projet où vous
voulez et lancez `launch.py` : le script rend lui-même le projet importable.
Pas de `pip install`, pas de `setup.py`, pas de `PYTHONPATH` à configurer.

### Prérequis

- Python 3.8 ou supérieur, avec `tkinter`
- Les bibliothèques `numpy`, `pandas`, `scipy` et `matplotlib`

Ces éléments sont déjà présents dans une installation Anaconda standard et
dans les installateurs officiels de Python pour Windows.

### Vérifier l'environnement

```bash
python launch.py --check
```

Le rapport indique la version de Python utilisée, la présence de chaque
bibliothèque et l'emplacement depuis lequel les modules du projet seront
chargés. C'est le premier réflexe en cas de problème.

### Si une bibliothèque manque

Une installation dans votre espace utilisateur ne demande aucun droit
administrateur :

```bash
pip install --user numpy pandas scipy matplotlib
```

## 💻 Utilisation

### Lancement de l'application

**Windows** : double-cliquez sur `run.bat`, ou sur `launch.py`.

**Linux / Mac** :
```bash
./run.sh
```

**Depuis un terminal**, quel que soit le répertoire courant :
```bash
python /chemin/vers/le/projet/launch.py
```

Avec Anaconda sous Windows, si `python` n'est pas reconnu dans l'invite de
commandes classique, ouvrez **Anaconda Prompt** puis :

```bash
cd /d C:\chemin\vers\le\projet
python launch.py
```

### Workflow

1. **Import du CSV** : Choisir un fichier CSV multi-colonnes et associer les colonnes à chaque inlet
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

### `ModuleNotFoundError: No module named 'core'` (ou `gui`)

Lancez toujours `launch.py`, jamais un fichier situé dans `src/` directement.
C'est `launch.py` qui rend les modules du projet importables.

### L'application ne démarre pas quand je double-clique

Lancez `run.bat` : la fenêtre reste ouverte et affiche l'erreur. Sinon,
exécutez `python launch.py --check` pour un diagnostic complet.

### `ModuleNotFoundError: No module named 'numpy'`

Le Python utilisé n'est pas celui d'Anaconda. `python launch.py --check`
affiche l'exécutable réellement employé. Ouvrez **Anaconda Prompt**, ou
installez les bibliothèques dans votre espace utilisateur :

```bash
pip install --user numpy pandas scipy matplotlib
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
