# Correctifs v2.0.1

## Problème résolu

### ImportError: attempted relative import beyond top-level package

**Cause** : Les imports relatifs (`from ..core import`) ne fonctionnent pas correctement lorsque le script est exécuté directement.

**Solution appliquée** :

1. **Conversion des imports relatifs en imports absolus** dans tous les modules :
   ```python
   # Avant
   from ..core.constants import FILE_KEYS
   
   # Après
   from core.constants import FILE_KEYS
   ```

2. **Création d'un script `launch.py`** à la racine qui configure le `sys.path` :
   ```python
   import sys
   import os
   
   project_root = os.path.dirname(os.path.abspath(__file__))
   src_path = os.path.join(project_root, 'src')
   sys.path.insert(0, src_path)
   
   from gui.app import run
   ```

3. **Modification de `src/main.py`** pour ajouter le chemin src au sys.path :
   ```python
   import sys
   import os
   
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   ```

## Fichiers modifiés

### Scripts de lancement
- ✅ `launch.py` - Nouveau script à la racine (recommandé)
- ✅ `run.sh` - Mis à jour pour utiliser `launch.py`
- ✅ `run.bat` - Mis à jour pour utiliser `launch.py`
- ✅ `Makefile` - Commande `make run` mise à jour

### Modules Python
- ✅ `src/main.py` - Ajout de la configuration du path
- ✅ `src/gui/app.py` - Imports absolus
- ✅ `src/gui/steps/step1_files.py` - Imports absolus
- ✅ `src/gui/steps/step2_params.py` - Imports absolus
- ✅ `src/gui/steps/step3_preview.py` - Imports absolus
- ✅ `src/gui/steps/step4_export.py` - Imports absolus

### Documentation
- ✅ `README.md` - Ajout de 4 méthodes de lancement
- ✅ `TROUBLESHOOTING.md` - Nouveau guide de dépannage
- ✅ `setup.py` - Configuration des packages corrigée

## Comment lancer l'application maintenant

### Méthode recommandée (la plus simple)

```bash
# Linux/Mac
./run.sh

# Windows
run.bat
```

### Autres méthodes

```bash
# Méthode 2 - Script Python
python launch.py

# Méthode 3 - Depuis src/
cd src
python main.py

# Méthode 4 - Make
make run
```

## Tests effectués

✅ Import des modules depuis la racine
✅ Import des modules depuis src/
✅ Lancement via launch.py
✅ Lancement via run.sh/run.bat
✅ Tous les imports résolus correctement

## Notes pour les développeurs

- Les imports absolus (sans `..`) sont maintenant utilisés partout
- Le script `launch.py` est le point d'entrée recommandé
- `src/main.py` peut toujours être utilisé depuis le répertoire `src/`
- Les tests unitaires utilisent également les imports absolus
