# Guide de dépannage

## Problèmes d'import Python

### Erreur : `ImportError: attempted relative import beyond top-level package`

**Solution** : Utilisez le script `launch.py` à la racine du projet au lieu de lancer directement `src/main.py`.

```bash
# ✅ Correct
python launch.py
# ou
./run.sh  # Linux/Mac
run.bat   # Windows

# ❌ Incorrect (depuis la racine)
python src/main.py
```

**Pourquoi ?** Les imports relatifs dans Python nécessitent que le package soit dans le `sys.path`. Le script `launch.py` configure automatiquement le chemin.

**Alternative** : Si vous voulez lancer depuis `src/` :
```bash
cd src
python main.py  # ✅ Fonctionne depuis le répertoire src
```

### Erreur : `ModuleNotFoundError: No module named 'core'`

**Solution** : Assurez-vous d'être à la racine du projet et utilisez `launch.py`.

```bash
# Vérifier que vous êtes à la racine
ls  # Vous devez voir : src/, tests/, launch.py, README.md, etc.

# Lancer l'application
python launch.py
```

## Problèmes de dépendances

### Erreur : `ModuleNotFoundError: No module named 'numpy'` (ou pandas, matplotlib, scipy)

**Solution** : Installez les dépendances.

```bash
pip install -r requirements.txt
```

### Sur Linux/Mac, erreur avec tkinter

**Solution** : Installez tkinter via le gestionnaire de paquets système.

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# macOS (avec Homebrew)
brew install python-tk
```

## Problèmes d'interface graphique

### L'application ne s'affiche pas

**Causes possibles** :
1. Pas d'environnement graphique (serveur SSH, WSL sans X11)
2. Tkinter non installé
3. Problème de permissions

**Solutions** :
- Sur WSL, installez un serveur X11 (VcXsrv, X410)
- Vérifiez que tkinter fonctionne :
  ```python
  python -c "import tkinter; tkinter.Tk()"
  ```

### Les graphiques matplotlib ne s'affichent pas

**Solution** : Vérifiez que matplotlib est installé avec le backend TkAgg.

```bash
pip install matplotlib --upgrade
```

## Problèmes de fichiers

### Erreur : "Impossible de lire le fichier CSV"

**Causes** :
- Format CSV non supporté
- Fichier corrompu
- Encodage incorrect

**Solutions** :
1. Vérifiez que le fichier contient exactement 2 colonnes
2. Séparateurs supportés : `,` `;` `\t` (tab) ou espaces
3. Essayez d'ouvrir le CSV dans Excel pour vérifier le format

### Erreur lors de l'export : "Permission denied"

**Solution** : Choisissez un emplacement où vous avez les droits d'écriture.

## Problèmes de tests

### Les tests ne se lancent pas

**Solution** : Installez les dépendances de développement.

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### Erreur : `pytest: command not found`

**Solution** : Installez pytest ou utilisez le module Python.

```bash
pip install pytest
# ou
python -m pytest tests/ -v
```

## Problèmes de performance

### L'application est lente lors de la prévisualisation

**Cause** : Trop de points à afficher.

**Solution** : Le code limite automatiquement à 5000 points pour la prévisualisation. Si c'est toujours lent :
1. Réduisez le pas de temps temporairement pour la configuration
2. Augmentez-le pour l'export final

### L'interpolation prend du temps

**Normal** : Avec beaucoup de points (>100 000), l'interpolation peut prendre quelques secondes.

## Besoin d'aide ?

Si votre problème n'est pas listé ici :

1. Vérifiez les logs d'erreur complets
2. Consultez le fichier `MANUAL_TESTS.md` pour des tests détaillés
3. Ouvrez une issue sur GitHub avec :
   - Version de Python (`python --version`)
   - Système d'exploitation
   - Message d'erreur complet
   - Étapes pour reproduire le problème
