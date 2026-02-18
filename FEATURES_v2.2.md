# Nouvelles fonctionnalités v2.2

## 🎯 Fonctionnalités ajoutées

### 1. Noms personnalisés pour les inlets dans le fichier .prof

**Problème résolu :** Les noms génériques "inlet1" et "inlet2" n'étaient pas descriptifs.

**Solution :** À l'étape 1, vous pouvez maintenant personnaliser les noms des inlets qui apparaîtront dans le fichier .prof exporté.

#### Interface

```
═══ Inlet 1 ═══
Nom pour l'export : [tulipe          ]  (ex: tulipe, main, primary...)
  Débit Inlet 1 (Q)       : [chemin/vers/data_Q_tulipe.csv]  [Parcourir...]
  Température Inlet 1 (T) : [chemin/vers/data_T_tulipe.csv]  [Parcourir...]

═══ Inlet 2 ═══
Nom pour l'export : [tige            ]  (ex: tige, secondary, aux...)
  Débit Inlet 2 (Q)       : [chemin/vers/data_Q_tige.csv]    [Parcourir...]
  Température Inlet 2 (T) : [chemin/vers/data_T_tige.csv]    [Parcourir...]
```

#### Résultat dans le fichier .prof

**Avant v2.2 :**
```
profile 5 1000 0
time Q_inlet1 T_inlet1 Q_inlet2 T_inlet2
0.0000000000 1.5 300.0 2.3 320.0
...
```

**Après v2.2 (avec noms "tulipe" et "tige") :**
```
profile 5 1000 0
time Q_tulipe T_tulipe Q_tige T_tige
0.0000000000 1.5 300.0 2.3 320.0
...
```

#### Caractéristiques
- ✅ Les espaces sont automatiquement remplacés par des underscores
- ✅ Les tirets sont remplacés par des underscores
- ✅ Les noms sont sauvegardés et restaurés lors de la navigation
- ✅ Noms par défaut : "inlet1" et "inlet2"

#### Exemples d'utilisation
- **Géométrie tulipe/tige** : `tulipe` et `tige`
- **Injection primaire/secondaire** : `primary` et `secondary`  
- **Configuration main/auxiliaire** : `main` et `aux`
- **Zones A/B** : `zone_A` et `zone_B`

---

### 2. Zones non-filtrées (interpolation exacte sélective)

**Problème résolu :** Parfois, certaines plages de temps nécessitent une précision absolue (transitoires rapides, événements critiques), tandis que d'autres bénéficient du lissage.

**Solution :** Définir des zones temporelles où l'interpolation sera **exacte** (PCHIP), même si la méthode Spline lissée est sélectionnée.

#### Interface

À l'étape 2, après les paramètres de lissage :

```
Zones non-filtrées (interpolation exacte)
Définir des plages de temps où le lissage est désactivé

[⚙️ Configurer zones Q (débits)     ]
  2 zone(s) définie(s)

[⚙️ Configurer zones T (températures)]
  Aucune zone définie
```

#### Dialogue de configuration

Cliquer sur le bouton ouvre un dialogue modal :

```
┌─ Zones non-filtrées pour les débits (Q) ──────────────────┐
│                                                             │
│  Définissez les plages de temps où l'interpolation doit    │
│  être EXACTE (sans lissage)                                │
│  Durée de simulation : 0.0 à 0.125000 s                    │
│                                                             │
│  ┌─ Zones définies ─────────────────────────────────────┐  │
│  │  [0.000000 → 0.010000] s                            │  │
│  │  [0.050000 → 0.060000] s                            │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [➕ Ajouter] [✏️ Modifier] [🗑️ Supprimer] [Vider tout]    │
│                                                             │
│                                        [Annuler]  [OK]      │
└─────────────────────────────────────────────────────────────┘
```

#### Fonctionnement

1. **Cliquer sur "➕ Ajouter"** → Saisir début et fin de la zone
2. **Zones validées** : Pas de chevauchement autorisé
3. **Effet** :
   - Dans les zones définies → **Interpolation PCHIP exacte**
   - En dehors des zones → **Interpolation selon la méthode choisie** (Spline lissée ou PCHIP)

#### Cas d'usage

##### Exemple 1 : Transitoire d'ouverture (0-10 ms)
```
Configuration :
- Méthode Q : Spline lissée, s=0.005
- Zones non-filtrées Q : [0.000, 0.010]

Résultat :
- 0 → 10 ms : Interpolation exacte (capture le transitoire précis)
- 10 ms → fin : Lissage appliqué (réduit le bruit)
```

##### Exemple 2 : Événement critique à mi-simulation
```
Configuration :
- Méthode T : Spline lissée, s=0.02
- Zones non-filtrées T : [0.050, 0.060]

Résultat :
- 0 → 50 ms : Lissage
- 50 → 60 ms : Interpolation exacte (événement thermique critique)
- 60 ms → fin : Lissage
```

##### Exemple 3 : Plusieurs zones critiques
```
Configuration :
- Méthode Q : Spline lissée, s=0.01
- Zones non-filtrées Q : [(0.0, 0.005), (0.045, 0.055), (0.095, 0.100)]

Résultat :
- Lissage général avec 3 zones d'interpolation exacte
```

#### Visualisation

Dans la prévisualisation de l'étape 2, les zones non-filtrées sont prises en compte :
- La courbe interpolée sera **exacte** dans les zones définies
- La courbe sera **lissée** en dehors

#### Algorithme

```python
Pour chaque point t dans times:
    Si t est dans une zone non-filtrée:
        valeur[t] = PCHIP(t)  # Interpolation exacte
    Sinon:
        valeur[t] = Spline_lissée(t)  # Avec paramètre de lissage
```

---

## 📋 Workflow complet

### Étape 1 : Sélection et nommage

1. **Sélectionner les 4 fichiers CSV**
2. **Personnaliser les noms** des deux inlets
   - Exemples : tulipe/tige, main/aux, primary/secondary
3. Cliquer sur **Suivant**

### Étape 2 : Configuration avancée

1. **Choisir les méthodes** d'interpolation (PCHIP ou Spline)
2. **Ajuster le lissage** (si Spline sélectionné)
3. **Définir les zones non-filtrées** (optionnel)
   - Cliquer sur "⚙️ Configurer zones Q"
   - Ajouter les plages critiques
   - Répéter pour les températures si nécessaire
4. **Observer la prévisualisation** en temps réel
5. Cliquer sur **Suivant**

### Étape 3 : Validation

- Vérifier les courbes finales (2×2)
- Retourner à l'étape 2 si ajustements nécessaires

### Étape 4 : Export

- Le fichier .prof utilisera les **noms personnalisés**
- Les zones non-filtrées sont **appliquées** aux données

---

## 🎨 Exemples visuels

### Effet des zones non-filtrées

**Sans zones (lissage uniforme) :**
```
Valeur ▲
       │     ╱╲              ╱╲
       │    ╱  ╲            ╱  ╲
       │   ╱    ╲          ╱    ╲
       │  ╱      ╲________╱      ╲
       │ ╱                        ╲
       └─────────────────────────────→ Temps
         Lissage partout
```

**Avec zone non-filtrée [0.0-0.01] :**
```
Valeur ▲
       │  ●╲  ╱╲              ╱╲
       │  ●●╲╱  ╲            ╱  ╲
       │  ●●●    ╲          ╱    ╲
       │  ●       ╲________╱      ╲
       │●                          ╲
       └─────────────────────────────→ Temps
         │        │
      Exact    Lissé
```

---

## 💡 Conseils d'utilisation

### Noms personnalisés

✅ **Bon** :
- `tulipe`, `tige`
- `main_inlet`, `aux_inlet`
- `primary`, `secondary`

❌ **Éviter** :
- Caractères spéciaux : `@`, `#`, `%`
- Espaces non convertis : `main inlet` → automatiquement `main_inlet`

### Zones non-filtrées

**Quand les utiliser :**
- ✅ Transitoires rapides d'ouverture/fermeture
- ✅ Événements thermiques critiques
- ✅ Phases de synchronisation précises
- ✅ Zones de mesure expérimentale à reproduire exactement

**Quand ne PAS les utiliser :**
- ❌ Données bruitées (utiliser plutôt le lissage global)
- ❌ Toute la simulation (utiliser PCHIP directement)

**Bonnes pratiques :**
- Garder les zones **courtes** (quelques % de la simulation totale)
- Ne pas se chevaucher
- Documenter la raison de chaque zone

---

## 🔧 Détails techniques

### Renommage des colonnes

Le renommage utilise un remplacement simple :
```python
"Q_inlet1" → "Q_tulipe"  # Si inlet1 → tulipe
"T_inlet2" → "T_tige"    # Si inlet2 → tige
```

### Gestion des zones

Les zones sont stockées comme liste de tuples :
```python
unfiltered_zones_Q = [(0.0, 0.01), (0.05, 0.06)]
unfiltered_zones_T = [(0.045, 0.055)]
```

### Performance

- Les zones n'impactent **pas** la performance de manière significative
- L'interpolation PCHIP et Spline sont toutes deux rapides
- Pour 100 000 points avec 3 zones : < 1 seconde

---

## 📝 Changelog v2.2

### Ajouté
- ✅ Noms personnalisés pour les inlets (étape 1)
- ✅ Zones non-filtrées configurables séparément pour Q et T
- ✅ Dialogue modal pour gérer les zones
- ✅ Validation des zones (pas de chevauchement)
- ✅ Labels de statut (nombre de zones)
- ✅ Sauvegarde et restauration des noms et zones

### Modifié
- Interface étape 1 : réorganisation par inlet avec champs de nom
- Interface étape 2 : ajout section "Zones non-filtrées"
- Fonction `interpolate_smooth` : support des zones non-filtrées
- Fonction `interpolate_all_data` : renommage automatique des colonnes

### Technique
- Nouveau fichier : `src/gui/unfiltered_zones_dialog.py`
- Mise à jour : 5 fichiers modifiés
- Tests : Compatible avec navigation flexible
