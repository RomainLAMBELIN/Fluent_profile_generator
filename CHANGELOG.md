# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [2.12.0]

### Ajouté
- Option « Inverser la courbe (×-1) » par courbe à l'étape 2 (appliquée à la prévisualisation et à l'export, y compris au remplacement des débits nuls)
- Décalage automatique de l'axe temporel : le premier instant mesuré devient 0 ms
- Deux inlets proposés par défaut dès l'ouverture de l'application, et quand l'auto-détection des colonnes ne reconnaît rien (nombre réglable par `DEFAULT_INLET_COUNT`)
- Nouveau dialogue de zones : liste des zones, sélection par cliquer-glisser sur le graphique, saisie des bornes, prévisualisation temps réel (sans zone / avec zones / zone en édition), bornes ajustées aux points de mesure
- Suite de tests `tests/` (toutes les combinaisons méthode × zones, continuité, extrapolation, grille non uniforme, inversion, décalage temporel)
- Affichage des dérivées à l'étape 2, activable ou non : les pentes des courbes brute et traitée sont tracées sous la courbe, avec la pente maximale de chacune, l'instant où elle est atteinte, et le pourcentage de réduction obtenu
- Repérage visuel de la pente maximale sur les deux panneaux (losange et trait pointillé), et bascule automatique en échelle logarithmique symétrique quand un pic isolé écrase le reste
- Rappel de la réduction de pente dans les titres de l'étape 3, au moment de la vérification avant export

### Corrigé
- Sauts de valeur aux frontières des zones avec Spline et Trend Filter : les segments sont désormais raccordés en valeur (continuité C0) et partagent leurs points frontière
- Trend Filter L1/L2 : les différences finies tiennent compte de l'espacement réel des temps (plus de pente aberrante entre deux mesures rapprochées, ex. 84.9 ms et 85.0 ms)
- Extrapolation polynomiale au-delà des données (PCHIP/Spline divergeaient) : prolongement constant
- Zones plus fines que le pas de mesure, chevauchantes ou hors plage : gestion explicite (élargies à 2 points, tronquées ou ignorées)
- Prévisualisation du dialogue de zones qui ne fonctionnait plus (arguments obsolètes passés à `interpolate()`), et lambda du Trend Filter non pris en compte dans cette prévisualisation
- Pas de temps du profil exporté désormais exactement égal à dt (`np.arange` au lieu de `linspace` avec arrondi)
- Bandeau d'informations de l'étape 2 non rafraîchi après modification des zones
- Panneau de paramètres de l'étape 2 tronqué à droite
- Plantage au démarrage (`KeyError: 'q_col'`) quand le fichier de configuration utilisateur provient d'une version antérieure : la configuration est désormais validée, et ignorée en bloc si elle est inutilisable, au lieu d'empêcher l'application de démarrer
- Noms d'inlets personnalisés perdus silencieusement au redémarrage : JSON ne stocke que des clés textuelles alors que le code les recherchait par index entier

### Modifié
- Trend Filter : résolution par matrices creuses (mémoire et temps réduits sur grandes séries)
- Évaluation des segments vectorisée (plus de boucle Python point par point)
- Suppression de `zone_editor_dialog.py` (fusionné dans `unfiltered_zones_dialog.py`)

## [2.11.0]

### Ajouté
- Transitions douces aux jonctions via interpolation cubique de Hermite (continuité C1)
- Distinction entre interpolation linéaire globale et linéaire de zone

### Modifié
- Suffixes `_global` et `_zone` dans `interpolate_with_zones()` pour différencier les types de segments
- Zones de transition de 2% avec Hermite pour éliminer les oscillations aux jonctions

## [2.10.1]

### Corrigé
- PCHIP et Linear ignoraient les zones définies : ajout de `interpolate_with_zones()` comme fonction universelle de segmentation

## [2.9.0]

### Ajouté
- Calcul d'erreur par intégrale (module `analysis.py`) avec affichage dans les titres des graphiques
- Toolbar matplotlib (zoom, pan, save) sur tous les graphiques
- Bandeau d'informations à l'étape 2 (durée, pas de temps, nombre de points, zones)
- Couleur noire pour l'interpolation linéaire de référence (meilleure visibilité)

## [2.8.1]

### Corrigé
- Sliders du dialogue de zone qui vidaient les Entry (`TclError`)
- Segmentation basée sur les indices de points au lieu des temps flottants (plus de trous)
- Bouton "Modifier" utilise maintenant `ZoneEditorDialog` avec prévisualisation

## [2.8.0]

### Ajouté
- Dialogue avancé `ZoneEditorDialog` avec sliders interactifs et prévisualisation temps réel
- Comparaison visuelle avec/sans zone dans le même graphique

### Corrigé
- Interpolation réellement segmentée : chaque segment a son propre interpolateur, éliminant les oscillations aux jonctions

## [2.7.0]

### Modifié
- Zone linéaire : droite entre les 2 points de borne uniquement (ignore les points intermédiaires)

## [2.6.1]

### Corrigé
- Taille du dialogue de zone agrandie (500x300) pour que les boutons soient visibles
- Centrage automatique du dialogue sur la fenêtre parent
- Raccourcis clavier : Entrée = OK, Échap = Annuler

## [2.6.0]

### Ajouté
- Sauvegarde automatique des fichiers et noms d'inlets (`ConfigManager`, `~/.fluent_prof_generator/config.json`)
- Chargement automatique des derniers fichiers au démarrage

### Corrigé
- Méthode par défaut changée en PCHIP (l'ancienne valeur "spline" causait une erreur)
- Conflit de noms `canvas` entre tkinter et matplotlib résolu

## [2.5.0]

### Ajouté
- Zones avec type d'interpolation : Exacte (PCHIP) ou Linéaire
- Transitions automatiques de 1% aux jonctions de zones (rampe linéaire)

### Corrigé
- Visibilité des graphiques : points réduits (3px), courbe plus épaisse (2.5px), couleurs différenciées
- Graphiques affichés dès le chargement de l'étape 2
- Étape 3 : courbes interpolées affichées avec nom de méthode et noms personnalisés

## [2.4.0]

### Modifié
- Configuration complètement indépendante par courbe (méthode, lissage, zones par courbe au lieu de global Q/T)
- Interface étape 2 réécrite avec sections par courbe et onglets séparés

## [2.3.0]

### Ajouté
- Zones non-filtrées indépendantes par inlet (4 boutons séparés)
- 3 nouvelles méthodes d'interpolation : Akima, Makima, Savitzky-Golay

## [2.2.0]

### Ajouté
- Noms personnalisés pour les inlets dans le fichier .prof
- Zones non-filtrées (interpolation exacte sélective) configurables séparément pour Q et T

## [2.1.0]

### Ajouté
- Choix de la méthode d'interpolation : PCHIP ou Spline lissée
- Lignes d'interpolation linéaire de référence (grises) dans les graphiques
- Interface adaptative : slider de lissage désactivé pour PCHIP

## [2.0.2]

### Corrigé
- Conversion complète de tous les imports relatifs en imports absolus
- `KeyError: 'dt_us'` à l'étape 2 : initialisation robuste des paramètres
- `IndexError` lors de la navigation : vérification d'existence du widget

## [2.0.1]

### Corrigé
- `ImportError: attempted relative import` : conversion des imports relatifs en absolus
- Création de `launch.py` comme point d'entrée recommandé

## [2.0.0] - 2026-01-30

### Ajouté
- Interface guidée en 4 étapes avec navigation flexible
- Visualisation interactive en temps réel lors du paramétrage
- Paramètres de lissage séparés pour débits (Q) et températures (T)
- Possibilité de revenir en arrière pour ajuster les paramètres
- Tests unitaires complets pour les modules core
- Documentation complète (README, CONTRIBUTING, MANUAL_TESTS)
- Configuration CI/CD avec GitHub Actions
- Scripts de lancement rapide (run.sh, run.bat)
- Makefile pour automatiser les tâches courantes

### Modifié
- Refactoring complet de l'architecture en modules séparés
- Amélioration de la lecture CSV avec détection automatique du format
- Utilisation de UnivariateSpline au lieu de PCHIP pour un meilleur contrôle du lissage
- Interface plus moderne et intuitive

### Supprimé
- Gestion de la mobilité (mob.csv) - fonctionnalité obsolète
- Gestion multi-dossiers remplacée par sélection directe des fichiers

## [1.0.0]

### Ajouté
- Version initiale avec interface basique
- Support des fichiers Q et T
- Interpolation PCHIP
- Export au format .prof
- Gestion de la mobilité
