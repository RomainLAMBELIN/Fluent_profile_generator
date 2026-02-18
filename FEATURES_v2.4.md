# Version 2.4 - Configuration indépendante par courbe

## 🎯 Changement majeur

**Avant v2.4 :** Méthode et lissage globaux pour tous les Q, globaux pour tous les T  
**Après v2.4 :** Méthode et lissage **complètement indépendants** pour chaque courbe

## 🎨 Nouvelle interface

### Vue d'ensemble

À l'étape 2, vous avez maintenant **4 sections indépendantes**, une pour chaque courbe :

```
┌─ Paramètres globaux ────────────────────┐
│ Pas de temps (µs)         : [1.0]       │
│ Remplacement débits nuls  : [1e-5]      │
└──────────────────────────────────────────┘

┌─ Débit tulipe ───────────────────────────┐
│ Méthode  : [Savitzky-Golay            ▼] │
│ Lissage  : [━━━●━━━━━━] 0.0050           │
│ [⚙️ Zones]  2 zone(s)                    │
└──────────────────────────────────────────┘

┌─ Température tulipe ─────────────────────┐
│ Méthode  : [PCHIP                     ▼] │
│ Lissage  : [━━━━━━━━━━] (désactivé)      │
│ [⚙️ Zones]  0 zone                       │
└──────────────────────────────────────────┘

┌─ Débit tige ─────────────────────────────┐
│ Méthode  : [Akima                     ▼] │
│ Lissage  : [━━━━━━━━━━] (désactivé)      │
│ [⚙️ Zones]  1 zone(s)                    │
└──────────────────────────────────────────┘

┌─ Température tige ───────────────────────┐
│ Méthode  : [Spline lissée             ▼] │
│ Lissage  : [━━━━━━━●━━] 0.0200           │
│ [⚙️ Zones]  0 zone                       │
└──────────────────────────────────────────┘

[⟳ Rafraîchir prévisualisations]
```

### Détails de chaque section

Chaque courbe a :
1. **Méthode d'interpolation** : Choix parmi 5 méthodes
2. **Paramètre de lissage** : Actif uniquement pour Spline et Savitzky-Golay
3. **Zones non-filtrées** : Configuration spécifique à cette courbe

## 💡 Cas d'usage

### Exemple 1 : Données de qualité différente

**Situation :**
- Q_inlet1 : Débitmètre précis, peu de bruit
- T_inlet1 : Thermocouple stable
- Q_inlet2 : Débitmètre ancien, beaucoup de bruit
- T_inlet2 : Thermocouple avec pics aberrants

**Configuration optimale :**
```
Q_inlet1 : PCHIP              (données propres → exact)
T_inlet1 : PCHIP              (données propres → exact)
Q_inlet2 : Savitzky-Golay     (filtre le bruit)
T_inlet2 : Makima             (robuste aux pics aberrants)
```

### Exemple 2 : Événements différents sur chaque inlet

**Situation :**
- Inlet 1 : Ouverture progressive, smooth
- Inlet 2 : Pulses rapides avec changements brusques

**Configuration optimale :**
```
Q_inlet1 : Spline lissée s=0.01   (ouverture smooth)
T_inlet1 : Spline lissée s=0.02   (gradients thermiques doux)
Q_inlet2 : Akima                  (capture pulses sans oscillations)
T_inlet2 : PCHIP + zones          (précision sur pics thermiques)
  Zones : [(0.010-0.015), (0.030-0.035)] → Chaque pulse
```

### Exemple 3 : Besoins CFD différents

**Situation :**
- Inlet 1 : Condition limite critique, besoin haute précision
- Inlet 2 : Condition secondaire, peut être lissée

**Configuration optimale :**
```
Q_inlet1 : PCHIP              (précision absolue)
T_inlet1 : PCHIP              (précision absolue)
Q_inlet2 : Spline s=0.02      (très lissé)
T_inlet2 : Spline s=0.03      (très lissé)
```

### Exemple 4 : Mix optimal selon physique

**Situation :**
- Débits : Signaux bruités mais prévisibles
- Températures inlet1 : Transitoire rapide au début
- Températures inlet2 : Stable avec pics isolés

**Configuration optimale :**
```
Q_inlet1 : Savitzky-Golay window=15  (fort filtrage)
Q_inlet2 : Savitzky-Golay window=15  (fort filtrage)
T_inlet1 : PCHIP + zone [0.0-0.01]   (transitoire initial exact)
T_inlet2 : Makima                    (filtre pics aberrants)
```

## 📊 Visualisation améliorée

### Onglets séparés

Les prévisualisations sont maintenant dans des **onglets séparés** :

```
┌─[Débit tulipe]─[Température tulipe]─[Débit tige]─[Température tige]────┐
│                                                                          │
│  Graphique avec :                                                       │
│  ━━━ Lignes linéaires (gris)                                           │
│  ●●● Points bruts                                                       │
│  ━━━ Courbe interpolée (méthode affichée dans légende)                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Comparaison rapide

Pour comparer les méthodes sur une courbe :
1. Sélectionner l'onglet de la courbe
2. Changer la méthode dans la combobox
3. Observer l'effet **instantanément**
4. Ajuster le lissage si besoin
5. Valider ou essayer une autre méthode

## 🔧 Workflow recommandé

### Étape par étape

**1. Charger les données (Étape 1)**
- Sélectionner les 4 fichiers CSV
- Personnaliser les noms des inlets

**2. Observer les données brutes (Étape 2)**
- Regarder chaque onglet
- Identifier le niveau de bruit/qualité de chaque courbe
- Noter les événements spéciaux (transitoires, pics, pulses)

**3. Choisir les méthodes (Étape 2)**
Pour chaque courbe, se demander :
```
• Données propres ?        → PCHIP
• Bruit haute fréquence ?  → Savitzky-Golay
• Changements brusques ?   → Akima
• Pics aberrants ?         → Makima
• Besoin contrôle fin ?    → Spline lissée
```

**4. Ajuster les paramètres (Étape 2)**
- Slider de lissage : observer l'effet en temps réel
- Zones non-filtrées : définir pour événements critiques
- Comparer avec lignes linéaires grises

**5. Valider globalement (Étape 3)**
- Vue 2×2 de toutes les courbes
- Vérifier cohérence
- Retour à étape 2 si ajustements nécessaires

**6. Exporter (Étape 4)**
- Fichier .prof avec noms personnalisés
- Configuration sauvegardée dans l'état

## 📐 Détails techniques

### Structure des paramètres

**Avant v2.4 :**
```python
params = {
    "method_Q": "spline",      # Pour TOUS les Q
    "method_T": "pchip",       # Pour TOUS les T
    "smooth_Q": 0.001,         # Pour TOUS les Q
    "smooth_T": 0.01,          # Pour TOUS les T
}
```

**Après v2.4 :**
```python
params = {
    "methods": {
        "Q_inlet1": "savgol",
        "T_inlet1": "pchip",
        "Q_inlet2": "akima",
        "T_inlet2": "spline",
    },
    "smooth_params": {
        "Q_inlet1": 0.005,
        "T_inlet1": 0.0,       # Pas utilisé (PCHIP)
        "Q_inlet2": 0.0,       # Pas utilisé (Akima)
        "T_inlet2": 0.02,
    },
    "unfiltered_zones": {
        "Q_inlet1": [(0.0, 0.01)],
        "T_inlet1": [],
        "Q_inlet2": [(0.05, 0.06)],
        "T_inlet2": [],
    }
}
```

### Migration automatique

Si vous avez des configurations v2.3 :
- Les anciens paramètres `method_Q/T` et `smooth_Q/T` sont convertis automatiquement
- Chaque courbe récupère les valeurs globales comme point de départ
- Vous pouvez ensuite les personnaliser individuellement

### Interface adaptative

Le slider de lissage s'active/désactive automatiquement :
- **Actif** pour : Spline, Savitzky-Golay
- **Désactivé** pour : PCHIP, Akima, Makima (méthodes exactes)

## 💾 Sauvegarde de configuration

Toutes les configurations sont sauvegardées dans l'état :
- Méthode de chaque courbe
- Lissage de chaque courbe
- Zones de chaque courbe
- Navigation arrière : tout est restauré

## 🎯 Avantages

### Flexibilité maximale

✅ **Adapter à la qualité des données** : Méthode robuste pour données bruitées, exacte pour données propres  
✅ **Optimiser par physique** : Différentes approches pour débits vs températures  
✅ **Gérer les événements locaux** : Zones et méthodes adaptées à chaque inlet  
✅ **Indépendance totale** : 4 courbes = 4 configurations complètement libres

### Simplicité d'utilisation

✅ **Interface scrollable** : Toutes les configurations visibles  
✅ **Prévisualisation temps réel** : Changement visible immédiatement  
✅ **Onglets séparés** : Focus sur une courbe à la fois  
✅ **Labels explicites** : Noms personnalisés (tulipe/tige) dans l'interface

### Puissance

✅ **5 méthodes** × 4 courbes = **20 combinaisons de base**  
✅ **Lissage ajustable** : De 0.0 à 0.1 par courbe  
✅ **Zones indépendantes** : Chaque courbe ses propres zones critiques  
✅ **Paramètres Savitzky-Golay** : Fenêtre et ordre configurables

## 📝 Changelog v2.4

### Modifié 🔧
- **Interface step2** : Complètement refaite avec sections par courbe
- **Paramètres** : Méthodes et lissage maintenant par courbe (dict)
- **Visualisation** : Onglets séparés au lieu d'onglets globaux
- **Code** : `step2_params.py` complètement réécrit (plus propre, plus maintenable)

### Ajouté ✨
- **Scrollbar** : Interface scrollable pour voir toutes les configurations
- **Bouton rafraîchir** : Mise à jour manuelle de toutes les prévis
- **Labels dynamiques** : Noms personnalisés des inlets dans l'interface

### Technique 📐
- Fonction `interpolate_all_data()` : Prend `methods` et `smooth_params` (dicts) au lieu de valeurs globales
- Structure params : Migration de `method_Q/T` vers `methods[key]`
- Interface : Canvas scrollable avec frame pour accueillir toutes les sections

### Rétrocompatibilité ⚠️
- Si anciens paramètres détectés, conversion automatique vers nouvelle structure
- Les valeurs `method_Q/T` et `smooth_Q/T` sont réparties sur les 4 courbes

## 🚀 Prochaines étapes possibles

### Fonctionnalités avancées envisageables

1. **Presets** : Sauvegarder/charger des configurations complètes
2. **Copie de config** : Copier les paramètres d'une courbe vers une autre
3. **Analyse automatique** : Suggérer la méthode selon le bruit détecté
4. **Export config** : Fichier JSON avec tous les paramètres
5. **Templates** : Configurations prédéfinies pour cas typiques

---

**C'est maintenant l'outil le plus flexible possible pour préparer vos données CFD !** 🎉

Chaque courbe est totalement indépendante et configurable selon vos besoins spécifiques.
