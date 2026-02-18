# Version 2.5 - Corrections et amélioration des zones

## 🐛 Bugs corrigés

### 1. Visibilité des graphiques améliorée

**Problème :** Difficile de distinguer les courbes dans la prévisualisation.

**Solution :**
- **Points bruts** : Réduits de 6px à **3px** (plus fins)
- **Courbe interpolée** : Augmentée de 2px à **2.5px** (plus épaisse)
- **Couleurs différenciées** : Points en bleu (C0), courbe en orange (C1)
- **Lignes linéaires** : Plus fines (0.8px) et plus transparentes (alpha=0.4)

**Résultat :** La courbe interpolée ressort beaucoup mieux !

### 2. Graphiques non affichés à l'étape 2

**Problème :** Au premier chargement de l'étape 2, aucun graphique n'apparaissait avant de changer une méthode.

**Solution :** Appel de `_update_preview()` dans le constructeur après `_build_ui()`.

**Résultat :** Les graphiques s'affichent immédiatement !

### 3. Prévisualisation finale (étape 3) incomplète

**Problème :** Seules les lignes linéaires et points bruts s'affichaient, pas les courbes interpolées.

**Cause :** Les clés dans `data_interp` sont renommées (ex: `Q_tulipe` au lieu de `Q_inlet1`).

**Solution :** 
- Conversion des clés avec les noms personnalisés
- Affichage du nom de la méthode dans la légende
- Ajout du paramètre de lissage pour Spline
- Titres avec noms personnalisés (ex: "Débit tulipe")

**Résultat :** Affichage complet avec toutes les informations !

## ✨ Nouvelles fonctionnalités

### 4. Zones avec interpolation linéaire forcée

**Problème :** Les zones permettaient seulement l'interpolation exacte (PCHIP).

**Solution :** Ajout d'un **type de zone** configurable :

#### Types de zones disponibles

**Zone Exacte (PCHIP)** :
- Passe exactement par tous les points de données
- Préserve la monotonie
- Utile pour : transitoires rapides, événements précis

**Zone Linéaire** :
- Lignes droites entre chaque point
- **Lissage manuel** contrôlé
- Utile pour : adoucir des pics, simplifier des zones complexes

#### Interface

Lors de la création/modification d'une zone :

```
┌─ Définir une zone ─────────────────────────┐
│                                             │
│  Plage de temps (0.0 à 0.125000 s)        │
│                                             │
│  Début (s) : [0.050000]                    │
│  Fin (s)   : [0.060000]                    │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  Type d'interpolation dans la zone :        │
│  ○ Exacte (PCHIP - passe par tous points) │
│  ● Linéaire (lignes droites entre points) │
│                                             │
│                          [Annuler]  [OK]    │
└─────────────────────────────────────────────┘
```

#### Affichage dans la liste

Les zones affichent maintenant leur type :

```
[0.000000 → 0.010000] Exacte
[0.050000 → 0.060000] Linéaire
[0.095000 → 0.100000] Exacte
```

### 5. Transitions lisses aux jonctions

**Problème :** Oscillations importantes aux jonctions entre zones et interpolation globale.

**Solution :** **Zone de transition automatique** de 1% de la largeur de la zone.

#### Algorithme de transition

```python
zone_width = t_end - t_start
transition_width = zone_width * 0.01  # 1% de chaque côté

Si t < t_start + transition_width:
    # Transition entrante (0 → 1)
    weight = (t - t_start) / transition_width
    
Si t > t_end - transition_width:
    # Transition sortante (1 → 0)
    weight = (t_end - t) / transition_width
    
Valeur finale = weight × valeur_zone + (1-weight) × valeur_lissée
```

#### Exemple visuel

**Avant (oscillations) :**
```
         Zone exacte
      ●────────────────●
     ╱                  ╲
────╱  ╱╲  ╱╲  ╱╲  ╱╲   ╲────
      ╱  ╲╱  ╲╱  ╲╱  ╲
     Oscillations aux jonctions
```

**Après (transitions) :**
```
         Zone exacte
      ●────────────────●
     ╱                  ╲
────╱                    ╲────
    ↑                    ↑
  Transition          Transition
  entrante            sortante
```

**Avantages :**
- ✅ Pas d'oscillations
- ✅ Connexion C1 (dérivée continue)
- ✅ Visuel plus propre
- ✅ Meilleure convergence CFD

## 💡 Cas d'usage des zones linéaires

### Exemple 1 : Adoucir un pic isolé

**Situation :** Un pic de température non physique (artéfact de mesure).

**Solution :**
```
Méthode globale : Spline s=0.01
Zone linéaire   : [0.045-0.055] couvrant le pic

Résultat : Le pic est "écrasé" par l'interpolation linéaire
```

### Exemple 2 : Simplifier une zone complexe

**Situation :** Zone avec beaucoup de petites oscillations non significatives.

**Solution :**
```
Méthode globale : PCHIP (exact)
Zone linéaire   : [0.060-0.080] pour simplifier

Résultat : Tendance générale préservée, détails lissés
```

### Exemple 3 : Créer une rampe contrôlée

**Situation :** Besoin d'une montée linéaire parfaite entre deux points.

**Solution :**
```
Méthode globale : Savitzky-Golay
Zone linéaire   : [0.000-0.020] rampe d'ouverture

Résultat : Rampe parfaitement linéaire
```

### Exemple 4 : Mix zones exactes et linéaires

**Configuration :**
```
Q_inlet1 :
  - Méthode : Spline s=0.005
  - Zone [0.000-0.005] Exacte    → Transitoire précis
  - Zone [0.040-0.050] Linéaire  → Lissage pic aberrant
  - Zone [0.095-0.100] Exacte    → Événement final précis
```

## 📊 Comparaison des types de zones

| Type | Passe par points | Lissage | Usage principal |
|------|-----------------|---------|-----------------|
| **Exacte (PCHIP)** | ✅ Tous | ❌ Non | Événements critiques, transitoires |
| **Linéaire** | ✅ Tous | ✅ Contrôlé | Adoucir pics, simplifier zones |

## 🔧 Détails techniques

### Structure des zones

**Ancien format (v2.4)** :
```python
zones = [
    (0.0, 0.01),       # tuple de 2 éléments
    (0.05, 0.06),
]
```

**Nouveau format (v2.5)** :
```python
zones = [
    (0.0, 0.01, "exact"),    # tuple de 3 éléments
    (0.05, 0.06, "linear"),
    (0.09, 0.10, "exact"),
]
```

**Rétrocompatibilité :** Les anciennes zones (2 éléments) sont automatiquement converties en zones exactes.

### Calcul de la transition

La transition est **linéaire** (rampe) :

```python
# Poids de 0 à 1
weight = distance_depuis_bord / largeur_transition

# Interpolation
valeur = weight * valeur_zone + (1 - weight) * valeur_globale
```

La largeur de transition (1%) évite les discontinuités tout en gardant la zone effective à ~98% de sa taille.

## 📝 Changelog v2.5

### Corrigé 🐛
- **Visibilité graphiques** : Points plus fins (3px), courbe plus épaisse (2.5px), couleurs différenciées
- **Affichage initial** : Graphiques affichés dès le chargement de l'étape 2
- **Step 3** : Courbes interpolées affichées avec nom de méthode et paramètres
- **Step 3** : Titres avec noms personnalisés des inlets
- **Oscillations zones** : Transitions automatiques de 1% aux jonctions

### Ajouté ✨
- **Zones linéaires** : Nouveau type de zone pour interpolation linéaire forcée
- **Sélecteur de type** : Radio buttons dans dialogue de zone
- **Affichage type** : Type de zone visible dans la liste
- **Transitions lisses** : Mélange progressif aux jonctions (évite oscillations)

### Modifié 🔧
- **Structure zones** : Tuple de 3 éléments (t_start, t_end, type)
- **Fonction `interpolate_smooth`** : Support zones linéaires + transitions
- **Dialogue zones** : Interface étendue avec choix du type
- **Step 3** : Affichage complet des informations

## 🎯 Workflow recommandé

### Utilisation des zones linéaires

1. **Observer les données** (étape 2) avec méthode globale
2. **Identifier les zones problématiques** :
   - Pics aberrants
   - Zones trop oscillantes
   - Besoin de rampes linéaires
3. **Créer des zones linéaires** pour ces zones
4. **Ajuster** la plage pour couvrir juste la zone à lisser
5. **Vérifier** l'effet dans la prévisualisation

### Combinaison zones exactes + linéaires

```
Exemple optimal :
- Début simulation    : Zone exacte (transitoire précis)
- Milieu avec artéfact: Zone linéaire (lissage)
- Fin simulation      : Zone exacte (événement final)
- Reste               : Méthode globale (Spline ou Akima)
```

## 🚀 Résultat

L'outil est maintenant **extrêmement précis et flexible** :
- ✅ Visibilité parfaite des prévisualisations
- ✅ Zones avec 2 types d'interpolation
- ✅ Transitions automatiques (pas d'oscillations)
- ✅ Contrôle total sur chaque aspect
- ✅ Interface complète et informative

**Parfait pour préparer des données CFD de haute qualité !** 🎉
