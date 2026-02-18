# Nouvelles fonctionnalités v2.3

## 🎯 Améliorations majeures

### 1. Zones non-filtrées **indépendantes par inlet**

**Problème résolu :** Les zones non-filtrées étaient globales pour tous les Q et tous les T, manquant de flexibilité.

**Solution :** Chaque inlet (Q_inlet1, T_inlet1, Q_inlet2, T_inlet2) a maintenant **ses propres zones non-filtrées**.

#### Interface

À l'étape 2, section "Zones non-filtrées (par inlet)" :

```
Zones non-filtrées (par inlet)
Définir des zones où l'interpolation est exacte pour chaque inlet

[⚙️ Q Inlet 1]  2 zone(s)
[⚙️ T Inlet 1]  0 zone
[⚙️ Q Inlet 2]  1 zone(s)
[⚙️ T Inlet 2]  3 zone(s)
```

#### Cas d'usage

**Exemple 1 : Transitoires différents**
```
Inlet 1 (tulipe) : Ouverture rapide à t=0
Inlet 2 (tige)   : Ouverture progressive à t=50ms

Configuration :
- Q_inlet1 : Zone [0.000, 0.010] → Capture transitoire rapide
- Q_inlet2 : Zone [0.050, 0.070] → Capture ouverture progressive
- T_inlet1 : Pas de zone (lissage partout)
- T_inlet2 : Zone [0.080, 0.090] → Pic thermique local
```

**Exemple 2 : Événement sur un seul inlet**
```
Inlet 1 : Débit constant, température stable
Inlet 2 : Injection pulsée avec pic thermique

Configuration :
- Q_inlet1 : Pas de zone
- T_inlet1 : Pas de zone
- Q_inlet2 : Zones [0.010-0.015], [0.030-0.035] → Pulses
- T_inlet2 : Zone [0.020-0.025] → Pic thermique
```

---

### 2. Nouvelles méthodes d'interpolation

**Avant v2.3 :** 2 méthodes (PCHIP, Spline lissée)  
**Après v2.3 :** 5 méthodes au choix !

#### 📊 Méthodes disponibles

##### 1. **PCHIP** (Piecewise Cubic Hermite Interpolating Polynomial)
```
Type       : Interpolation exacte
Avantages  : Préserve la monotonie, pas d'oscillations
Paramètres : Aucun (toujours exact)
Idéal pour : Données propres, besoin de fidélité absolue
```

##### 2. **Spline lissée** (UnivariateSpline)
```
Type       : Interpolation avec lissage contrôlable
Avantages  : Très flexible, paramètre de lissage ajustable
Paramètres : Facteur de lissage (0 = exact, 0.001-0.1 = lissage)
Idéal pour : Usage général, contrôle fin du lissage
```

##### 3. **Akima** ⭐ NOUVEAU
```
Type       : Interpolation cubique locale
Avantages  : Minimise les oscillations, robuste aux changements brusques
Paramètres : Aucun
Idéal pour : Données avec changements de pente soudains, 
             discontinuités locales
```

##### 4. **Makima** (Modified Akima) ⭐ NOUVEAU
```
Type       : Akima améliorée
Avantages  : Plus robuste aux valeurs aberrantes, meilleure pour 
             données non uniformes
Paramètres : Aucun
Idéal pour : Données bruitées avec pics isolés, 
             distributions irrégulières
```

##### 5. **Savitzky-Golay** ⭐ NOUVEAU
```
Type       : Filtre polynomial par fenêtre glissante
Avantages  : Excellent pour réduire bruit haute fréquence,
             préserve les pics et la forme générale
Paramètres : Taille de fenêtre (défaut: 11), ordre polynomial (défaut: 3)
Idéal pour : Signaux bruités avec structure claire,
             besoin de filtrage passe-bas
```

---

## 📋 Guide de sélection de la méthode

### Arbre de décision

```
Mes données sont-elles bruitées ?
│
├─ NON → Données propres, peu de points
│   └─ Utiliser PCHIP (interpolation exacte)
│
└─ OUI → Données bruitées
    │
    ├─ Bruit haute fréquence, structure claire ?
    │   └─ Utiliser Savitzky-Golay (excellent filtrage)
    │
    ├─ Changements brusques de pente ?
    │   └─ Utiliser Akima (pas d'oscillations)
    │
    ├─ Valeurs aberrantes, pics isolés ?
    │   └─ Utiliser Makima (robuste)
    │
    └─ Besoin de contrôle fin du lissage ?
        └─ Utiliser Spline lissée (très flexible)
```

### Comparaison visuelle

**Signal avec bruit :**
```
PCHIP       : ●───●──●────●───●  (suit tous les points, bruit inclus)
Spline s=0.01: ──────────────── (lisse, contrôlable)
Akima       : ────●────●─────●─ (local, suit les tendances)
Makima      : ───────────────── (comme Akima, plus robuste)
Savgol      : ════════════════ (très lisse, préserve forme)
```

**Signal avec saut :**
```
PCHIP       : ──────┐
             : ──────│──────    (suit le saut)
Spline      : ─────╱╲──────    (peut osciller)
Akima       : ──────│──────    (suit bien, pas d'overshoot)
Makima      : ──────│──────    (suit bien)
Savgol      : ─────╱ ╲─────    (adoucit le saut)
```

---

## 🎨 Exemples d'application CFD

### Cas 1 : Injection avec transitoire d'ouverture

**Problématique :** 
- Ouverture rapide avec bruit de capteur
- Besoin de précision au début, lissage ensuite

**Configuration :**
```
Q_inlet1:
- Méthode : Savitzky-Golay (filtre le bruit)
- Zone non-filtrée : [0.000, 0.005] → Interpolation PCHIP exacte au démarrage

Q_inlet2:
- Méthode : Spline lissée, s=0.005
- Pas de zone non-filtrée
```

### Cas 2 : Températures avec pics thermiques

**Problématique :**
- Signal température avec pics isolés (valeurs aberrantes)
- Pics réels à préserver vs pics aberrants à filtrer

**Configuration :**
```
T_inlet1:
- Méthode : Makima (robuste aux aberrations)
- Zone non-filtrée : [0.050, 0.055] → Préserver pic thermique réel

T_inlet2:
- Méthode : Makima
- Pas de zone (filtrage des pics aberrants partout)
```

### Cas 3 : Débits pulsés

**Problématique :**
- Injections périodiques avec montées/descentes rapides
- Éviter les oscillations entre les pulses

**Configuration :**
```
Q_inlet1:
- Méthode : Akima (pas d'oscillations)
- Zones non-filtrées : Multiple zones pour chaque pulse
  [(0.000-0.002), (0.010-0.012), (0.020-0.022), ...]
```

---

## 🔧 Détails techniques

### Akima vs Makima

**Akima :**
- Interpolation locale (n'utilise que 5 points voisins)
- Formule : dérivées calculées à partir des pentes locales
- Avantage : Pas d'influence globale → pas d'oscillations lointaines

**Makima :**
- Modification des poids dans le calcul des dérivées
- Plus résistant aux "outliers" (valeurs aberrantes)
- Préféré pour données expérimentales réelles

### Savitzky-Golay

**Principe :**
1. Fenêtre glissante de N points (N impair)
2. Ajustement polynomial de degré P
3. Évaluation au centre de la fenêtre
4. Déplacement de la fenêtre

**Paramètres :**
- `window_length` : Taille de fenêtre (plus grand = plus lisse)
- `polyorder` : Degré polynomial (2-3 typique)

**Recommandations :**
- Signal lisse → window=7-11, polyorder=2
- Signal avec pics → window=11-15, polyorder=3
- Très bruité → window=21-31, polyorder=3

---

## 💡 Conseils d'utilisation

### Zones non-filtrées par inlet

**Bonnes pratiques :**
- ✅ Définir zones uniquement pour les inlets concernés
- ✅ Garder zones courtes (< 10% durée simulation chacune)
- ✅ Documenter la raison physique de chaque zone
- ✅ Tester avec/sans zones pour valider l'impact

**Exemples de zones pertinentes :**
- Transitoires d'ouverture/fermeture de vanne
- Pics de pression ou température mesurés expérimentalement
- Synchronisation temporelle avec équipement externe
- Phases critiques identifiées en post-traitement

**À éviter :**
- ❌ Zones couvrant > 50% de la simulation (utiliser PCHIP directement)
- ❌ Zones pour "lisser moins" (ajuster plutôt le paramètre de lissage)
- ❌ Zones sur tous les inlets identiques (utiliser zones Q/T globales à la place)

### Choix de la méthode

**Pour débuter :**
1. Charger les données, observer les courbes brutes (étape 2)
2. Essayer **PCHIP** → Voir si acceptable ou trop bruité
3. Si trop bruité :
   - Essayer **Savitzky-Golay** pour fort bruit HF
   - Essayer **Akima/Makima** pour pics et sauts
   - Essayer **Spline** si besoin contrôle fin

**Comparaison rapide :**
- Changer méthode → Observer prévi temps réel
- Comparer avec lignes linéaires grises
- Vérifier gradients (zoom sur zones critiques)

---

## 📝 Changelog v2.3

### Ajouté ⭐
- ✅ **Zones non-filtrées par inlet** (4 boutons séparés)
- ✅ **3 nouvelles méthodes d'interpolation** :
  - Akima (minimise oscillations)
  - Makima (robuste aux aberrations)
  - Savitzky-Golay (filtre polynomial)
- ✅ Descriptions d'aide pour chaque méthode
- ✅ Support Savitzky-Golay avec paramètres configurables

### Modifié 🔧
- Structure zones : `dict` par inlet au lieu de 2 listes Q/T
- Interface étape 2 : 4 boutons de configuration (Q1, T1, Q2, T2)
- Noms de zones dans dialogues : affiche nom personnalisé inlet
- Fonction `interpolate()` : support 5 méthodes
- Fonction `interpolate_all_data()` : zones en dict, params Savgol

### Technique 📐
- Nouveaux imports : `Akima1DInterpolator`, `savgol_filter`
- 3 nouvelles fonctions : `interpolate_akima()`, `interpolate_makima()`, `interpolate_savgol()`
- Constantes : `INTERP_METHODS_HELP`, `DEFAULT_SAVGOL_*`
- Rétrocompatibilité : fallback PCHIP si < 5 points pour Akima/Makima

---

## 🚀 Migration depuis v2.2

Si vous avez des configurations sauvegardées v2.2 :

**Zones :**
```python
# v2.2
"unfiltered_zones_Q": [(0.0, 0.01)]
"unfiltered_zones_T": [(0.05, 0.06)]

# v2.3 (conversion automatique au premier lancement)
"unfiltered_zones": {
    "Q_inlet1": [(0.0, 0.01)],
    "T_inlet1": [(0.05, 0.06)],
    "Q_inlet2": [(0.0, 0.01)],
    "T_inlet2": [(0.05, 0.06)],
}
```

**Méthodes :**
- `"pchip"` et `"spline"` : fonctionnent toujours
- Nouvelles : `"akima"`, `"makima"`, `"savgol"` disponibles

---

## 📚 Ressources

### Documentation scipy
- PCHIP : `scipy.interpolate.PchipInterpolator`
- Spline : `scipy.interpolate.UnivariateSpline`
- Akima : `scipy.interpolate.Akima1DInterpolator`
- Savitzky-Golay : `scipy.signal.savgol_filter`

### Articles de référence
- Akima (1970) : "A New Method of Interpolation and Smooth Curve Fitting"
- Savitzky & Golay (1964) : "Smoothing and Differentiation of Data"

---

C'est la version la plus complète et flexible à ce jour ! 🎉
