# Version 2.6 - Sauvegarde automatique et corrections

## 🐛 Bugs corrigés

### 1. Erreur "list index out of range"

**Problème :** Au premier affichage de l'étape 2, erreur car la méthode par défaut "spline" n'existe pas (c'est "Spline lissée (avec paramètre de lissage)").

**Solution :**
- Méthode par défaut changée en **"pchip"** au lieu de "spline"
- Gestion robuste dans `_update_preview()` : si la méthode n'est pas trouvée, utiliser PCHIP par défaut
- Mise à jour automatique de la variable si méthode invalide

**Résultat :** Affichage correct dès le premier chargement !

### 2. Conflit de noms "canvas"

**Problème :** Erreur `'FigureCanvasTkAgg' object has no attribute 'configure'`

**Cause :** Deux variables nommées `canvas` :
- Le `tk.Canvas` pour le scroll
- Les `FigureCanvasTkAgg` pour matplotlib

**Solution :** Renommer le canvas de scroll en `scroll_canvas`

```python
# Avant
canvas = tk.Canvas(...)
canvas.configure(...)

# Après
scroll_canvas = tk.Canvas(...)
scroll_canvas.configure(...)
```

**Résultat :** Plus d'erreurs de conflit !

## ✨ Nouvelle fonctionnalité : Sauvegarde automatique

### Chargement automatique des derniers fichiers

**Problème :** À chaque lancement, il fallait re-sélectionner les 4 fichiers CSV.

**Solution :** Système de configuration persistante

#### Fonctionnement

1. **Premier lancement** : Sélectionner les fichiers normalement
2. **Validation de l'étape 1** : Les fichiers sont automatiquement sauvegardés
3. **Prochains lancements** : Les champs sont **pré-remplis** avec les derniers fichiers !

#### Emplacement

Le fichier de configuration est créé dans :
```
Windows : C:\Users\<username>\.fluent_prof_generator\config.json
Linux   : /home/<username>/.fluent_prof_generator/config.json
Mac     : /Users/<username>/.fluent_prof_generator/config.json
```

#### Contenu du fichier config.json

```json
{
  "last_files": {
    "Q_inlet1": "C:/data/Q_tulipe.csv",
    "T_inlet1": "C:/data/T_tulipe.csv",
    "Q_inlet2": "C:/data/Q_tige.csv",
    "T_inlet2": "C:/data/T_tige.csv"
  },
  "last_inlet_names": {
    "inlet1": "tulipe",
    "inlet2": "tige"
  },
  "last_export_dir": "C:/exports"
}
```

#### Ce qui est sauvegardé

✅ **Chemins des 4 fichiers CSV** : Si les fichiers existent toujours  
✅ **Noms personnalisés des inlets** : "tulipe", "tige", etc.  
✅ **Dernier répertoire d'export** : Pour l'étape 4 (à implémenter)

#### Sécurité

- Vérification d'existence : seuls les fichiers encore présents sur le disque sont chargés
- Pas de crash si le fichier config est corrompu
- Fichier JSON lisible et éditable manuellement

### Workflow amélioré

**Premier run :**
```
1. Lancer l'application
2. Sélectionner les 4 fichiers CSV
3. Personnaliser les noms (tulipe/tige)
4. Cliquer "Suivant"
   → Sauvegarde automatique dans config.json
```

**Runs suivants :**
```
1. Lancer l'application
2. Étape 1 pré-remplie avec derniers fichiers ✨
3. Vérifier/ajuster si besoin
4. Cliquer "Suivant" directement !
```

**Gain de temps énorme sur workflows répétitifs !**

## 🔧 Module de configuration

### Classe ConfigManager

```python
from core.config import ConfigManager

config = ConfigManager()

# Charger derniers fichiers
last_files = config.get_last_files()

# Sauvegarder fichiers
config.save_last_files({
    "Q_inlet1": "/path/to/Q1.csv",
    ...
})

# Charger/sauvegarder noms inlets
inlet_names = config.get_last_inlet_names()
config.save_last_inlet_names({"inlet1": "tulipe", ...})

# Dernier répertoire d'export
export_dir = config.get_last_export_dir()
config.save_last_export_dir("/path/to/exports")
```

### Méthodes disponibles

| Méthode | Description |
|---------|-------------|
| `get_last_files()` | Récupère dict des derniers fichiers |
| `save_last_files(files)` | Sauvegarde les fichiers |
| `get_last_inlet_names()` | Récupère derniers noms inlets |
| `save_last_inlet_names(names)` | Sauvegarde noms inlets |
| `get_last_export_dir()` | Récupère dernier répertoire export |
| `save_last_export_dir(dir)` | Sauvegarde répertoire export |

## 📝 Changelog v2.6

### Corrigé 🐛
- **Méthode par défaut** : PCHIP au lieu de "spline" (qui n'existe pas)
- **Gestion robuste** : Fallback sur PCHIP si méthode invalide
- **Conflit canvas** : Renommage `scroll_canvas` pour éviter conflit avec matplotlib
- **Affichage initial** : Fonctionne correctement dès le premier chargement

### Ajouté ✨
- **ConfigManager** : Module de gestion de configuration (`src/core/config.py`)
- **Sauvegarde auto** : Fichiers et noms d'inlets sauvegardés après validation étape 1
- **Chargement auto** : Derniers fichiers chargés au démarrage
- **Fichier config** : `.fluent_prof_generator/config.json` dans home directory

### Modifié 🔧
- **app.py** : Intégration ConfigManager dans __init__
- **app.py** : Sauvegarde après validation étape 1
- **constants.py** : DEFAULT_INTERP_METHOD = "pchip"
- **step2_params.py** : Gestion erreur méthode invalide

## 💡 Cas d'usage

### Workflow répétitif quotidien

**Situation :** Vous traitez les mêmes fichiers plusieurs fois par jour avec différents paramètres.

**Avant v2.6 :**
```
Chaque lancement :
1. Sélectionner Q_inlet1.csv
2. Sélectionner T_inlet1.csv
3. Sélectionner Q_inlet2.csv
4. Sélectionner T_inlet2.csv
5. Taper "tulipe"
6. Taper "tige"
7. Configurer...
```

**Après v2.6 :**
```
Premier lancement de la journée :
1-6. [comme avant]
7. Configurer...

Lancements suivants :
1. ✨ Tout pré-rempli !
2. Ajuster paramètres directement
```

### Changement de fichiers occasionnel

Si vous voulez charger d'autres fichiers :
1. Cliquer "Parcourir..." pour chaque fichier
2. Les nouveaux chemins remplaceront les anciens
3. Seront sauvegardés pour la prochaine fois

### Partage de configuration

Le fichier `config.json` peut être copié/partagé :
```bash
# Sauvegarder ma config
cp ~/.fluent_prof_generator/config.json backup_config.json

# Restaurer ou partager
cp backup_config.json ~/.fluent_prof_generator/config.json
```

## 🔒 Vie privée

Le fichier de configuration contient :
- Chemins de fichiers locaux (relatifs à votre machine)
- Noms personnalisés que vous avez choisis
- **Aucune donnée sensible**
- **Jamais envoyé nulle part**

Vous pouvez :
- Le supprimer (`rm ~/.fluent_prof_generator/config.json`)
- L'éditer manuellement (format JSON simple)
- L'ignorer (l'appli fonctionne sans)

## 🎯 Prochaines améliorations possibles

- [ ] Sauvegarder aussi les paramètres d'interpolation préférés
- [ ] Historique des configurations (plusieurs profils)
- [ ] Import/export de configurations
- [ ] Templates de configuration pour cas typiques

---

**L'application est maintenant beaucoup plus agréable pour un usage répétitif !** 🚀
