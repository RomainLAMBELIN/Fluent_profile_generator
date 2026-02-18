# Version 2.9 - Amélioration de l'analyse et de l'interface

## ✨ Nouvelles fonctionnalités

### 1. Couleur noire pour l'interpolation linéaire de référence

**Changement :** Les lignes d'interpolation linéaire (référence) sont maintenant en **noir** au lieu de gris clair.

**Raison :** Meilleure visibilité et distinction claire avec les courbes interpolées.

**Où :**
- ✅ Étape 2 : Prévisualisations
- ✅ Étape 3 : Prévisualisation finale
- ✅ Dialogue de zone : Comparaison

**Aspect visuel :**
```
Avant : ─── Gris clair (difficile à voir)
Après : ─── Noir (bien visible)
```

### 2. Zoom interactif sur tous les graphiques

**Nouvelle toolbar matplotlib** ajoutée sur tous les graphiques !

**Fonctionnalités disponibles :**
- 🏠 **Home** : Retour à la vue initiale
- ← → **Pan** : Déplacer la vue (clic + glisser)
- 🔍 **Zoom** : Zoomer sur une zone (sélection rectangle)
- ⚙️ **Configure** : Ajuster marges, limites
- 💾 **Save** : Sauvegarder l'image

**Utilisation :**
```
1. Cliquer sur l'icône Zoom (loupe)
2. Tracer un rectangle sur la zone à agrandir
3. Relâcher → Zone agrandie !
4. Cliquer Home pour revenir
```

**Où disponible :**
- ✅ Étape 2 : Sur chaque onglet (4 graphiques)
- ✅ Dialogue de zone : Graphique de prévisualisation

**Avantage :** Examiner en détail les zones problématiques, transitions, oscillations !

### 3. Bandeau d'informations à l'étape 2

**Nouveau bandeau** en haut de l'étape 2 affichant :

```
📊 Durée simulation : 0.125000 s  |  ⏱️ Pas de temps : 1.00e-06 s (1.00 µs)  |  📈 Points interpolés : 125,001  |  🎯 Zones définies : 3
```

**Informations affichées :**
- 📊 **Durée simulation** : Durée totale (du fichier le plus long)
- ⏱️ **Pas de temps** : En secondes et en microsecondes
- 📈 **Points interpolés** : Nombre total de points générés
- 🎯 **Zones définies** : Nombre total de zones sur toutes les courbes

**Mise à jour automatique :**
- Changement du pas de temps → Recalcul automatique
- Ajout/suppression de zone → Compteur mis à jour

**Couleur :** Bleu pour bien se distinguer

### 4. Calcul d'erreur par intégrale

**Nouveau module** : `src/core/analysis.py`

#### Méthode de calcul

**Principe :** Comparer l'aire sous les courbes

```
Intégrale données brutes (linéaire entre points)
              vs
Intégrale données interpolées

Erreur relative = |I_interp - I_raw| / |I_raw| × 100%
```

**Formule :**
```python
# Intégrale par méthode des trapèzes
I_raw = ∫ f_linéaire(t) dt  # Entre chaque point
I_interp = ∫ f_interpolée(t) dt  # Spline, PCHIP, etc.

Erreur absolue = |I_interp - I_raw|
Erreur relative = (Erreur absolue / |I_raw|) × 100%
```

#### Affichage

**Dans l'étape 2 :**
```
Titre de chaque graphique :
Q_inlet1 - Erreur: 0.245% (abs: 1.23e-04)
```

**Dans le dialogue de zone :**
```
Titre avec comparaison :
Effet de la zone (rouge) sur l'interpolation
Sans zone: Erreur: 1.523% (abs: 3.45e-03) | Avec zone: Erreur: 0.087% (abs: 1.98e-04)
```

#### Interprétation

**Erreur < 0.1%** : ✅ Excellente précision  
**Erreur 0.1-1%** : ✅ Bonne précision  
**Erreur 1-5%** : ⚠️ Acceptable, vérifier  
**Erreur > 5%** : ❌ Importante déviation, ajuster paramètres

#### Cas particuliers

**Intégrale nulle ou très petite :**
- Si `|I_raw| < 1e-10` → Affiche seulement erreur absolue
- Évite division par zéro

**Signal oscillant autour de zéro :**
- L'intégrale peut être petite même si le signal est grand
- L'erreur absolue reste informative

## 📊 Exemples d'utilisation

### Exemple 1 : Vérifier l'impact du lissage

```
Étape 2 → Q_inlet1

Spline s=0.001 → Titre: "Erreur: 0.045%"
Spline s=0.01  → Titre: "Erreur: 1.234%"
Spline s=0.05  → Titre: "Erreur: 5.678%"

→ s=0.001 est optimal (très faible erreur)
```

### Exemple 2 : Impact d'une zone linéaire

```
Dialogue de zone [0.048-0.052] Linéaire

Sans zone: Erreur: 2.345%
Avec zone: Erreur: 0.123%

→ La zone linéaire AMÉLIORE la précision !
  (Elle saute le pic aberrant)
```

### Exemple 3 : Choix de méthode

```
Étape 2 → T_inlet1

PCHIP       → Erreur: 0.001%  ← Excellent
Spline s=0  → Erreur: 0.001%
Akima       → Erreur: 0.002%
Spline s=0.05 → Erreur: 3.456%  ← Trop lissé

→ PCHIP ou Akima recommandés
```

### Exemple 4 : Zoom sur transition

```
1. Créer zone [0.01-0.02] Linéaire
2. Observer prévisualisation
3. Cliquer Zoom
4. Tracer rectangle autour de t=0.01
5. Examiner la transition en détail
6. Ajuster les bornes si oscillations
```

## 🔧 Détails techniques

### Module analysis.py

```python
from core.analysis import compute_interpolation_error, format_error_text

# Calculer erreur
error = compute_interpolation_error(df, times, interpolated)

# Retourne dict :
{
    'relative_error_percent': 0.245,
    'absolute_error': 1.23e-04,
    'raw_integral': 0.05023,
    'interp_integral': 0.05035
}

# Formater pour affichage
text = format_error_text(error)  # "Erreur: 0.245% (abs: 1.23e-04)"
```

### Toolbar matplotlib

```python
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

# Ajouter toolbar
toolbar = NavigationToolbar2Tk(canvas, parent_frame)
toolbar.update()
```

**Boutons disponibles :**
- Home, Back, Forward : Navigation
- Pan, Zoom : Manipulation vue
- Configure subplots : Ajustements
- Save : Export image

## 📝 Changelog v2.9

### Ajouté ✨
- **Couleur noire** : Interpolation linéaire référence en noir (meilleure visibilité)
- **Toolbar matplotlib** : Zoom interactif sur tous les graphiques
- **Bandeau d'infos** : Étape 2 affiche durée, dt, points, zones
- **Calcul d'erreur** : Module `analysis.py` avec intégration
- **Erreur dans titres** : Affichage erreur sur chaque graphique
- **Comparaison erreurs** : Dialogue zone montre erreur avec/sans zone

### Modifié 🔧
- **step2_params.py** : Bandeau info, toolbar, affichage erreur
- **step3_preview.py** : Couleur noire pour référence
- **zone_editor_dialog.py** : Toolbar, affichage erreur comparatif
- **Imports** : Ajout de `scipy.integrate.trapezoid`

### Nouveau fichier 📄
- **src/core/analysis.py** : Fonctions de calcul d'erreur

## 💡 Workflow recommandé

### Optimiser les paramètres avec l'erreur

```
1. Charger données (Étape 1)
2. Aller Étape 2
3. Regarder bandeau : nombre de points, zones
4. Pour chaque courbe :
   a. Observer titre : erreur actuelle
   b. Changer méthode → Voir erreur changer
   c. Ajuster lissage → Minimiser erreur
   d. Ajouter zones si besoin
   e. Utiliser zoom pour examiner détails
5. Erreur < 1% partout ? → Continuer !
```

### Définir zones optimales

```
1. [⚙️ Zones] pour une courbe
2. [➕ Ajouter]
3. Dialogue s'ouvre avec erreur de base
4. Bouger sliders :
   - Observer courbe
   - Observer erreur "Avec zone"
5. Type Exacte vs Linéaire :
   - Comparer les erreurs
   - Choisir celle qui minimise
6. Utiliser zoom pour vérifier transitions
7. [OK] quand erreur satisfaisante
```

## 🎯 Objectifs de précision

**Pour des simulations CFD :**

**Débits (Q) :**
- ✅ Erreur < 0.5% : Excellent (masse conservée)
- ⚠️ Erreur 0.5-2% : Acceptable
- ❌ Erreur > 2% : Revoir interpolation

**Températures (T) :**
- ✅ Erreur < 1% : Excellent (énergie conservée)
- ⚠️ Erreur 1-5% : Acceptable selon cas
- ❌ Erreur > 5% : Revoir interpolation

**Zones critiques :**
- Utiliser zones "Exacte" pour conserver intégrale
- Zones "Linéaire" peuvent augmenter erreur mais éliminer artéfacts

---

**L'outil est maintenant ultra-précis et ultra-visuel !** 🎉

Tu peux :
- ✅ Voir exactement l'erreur introduite
- ✅ Zoomer pour examiner en détail
- ✅ Optimiser facilement les paramètres
- ✅ Avoir toutes les infos en un coup d'œil
