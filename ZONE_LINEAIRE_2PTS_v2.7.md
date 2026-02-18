# Zone Linéaire - Interpolation entre 2 points de borne

## 🎯 Concept

La zone de type **"Linéaire"** trace maintenant une **droite entre seulement les 2 points de borne**, en **ignorant complètement** tous les points intermédiaires.

### Comportement

```
Données brutes dans la zone [t1, t6] :
●────────●────────●────────●────────●────────●
t1       t2       t3       t4       t5       t6
v1       v2       v3       v4       v5       v6
```

**Zone Exacte (PCHIP)** : Passe par tous les points
```
●────────●────────●────────●────────●────────●
 ╲      ╱ ╲      ╱ ╲      ╱ ╲      ╱ ╲      ╱
  ╲    ╱   ╲    ╱   ╲    ╱   ╲    ╱   ╲    ╱
   ╲  ╱     ╲  ╱     ╲  ╱     ╲  ╱     ╲  ╱
    ╲╱       ╲╱       ╲╱       ╲╱       ╲╱
```

**Zone Linéaire (nouveau comportement)** : Droite entre t1 et t6 UNIQUEMENT
```
●                                           ●
 ╲                                         ╱
  ╲                                       ╱
   ╲           Points 2,3,4,5            ╱
    ╲          IGNORÉS !                ╱
     ╲                                 ╱
      ╲                               ╱
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 💡 Cas d'usage

### 1. Éliminer un pic aberrant avec points autour

**Situation :**
```
Données avec pic aberrant à t=0.05s entouré de points bruités :

t=0.048s : v=100.2
t=0.049s : v=102.5
t=0.050s : v=450.0  ← Pic aberrant
t=0.051s : v=98.7
t=0.052s : v=101.3
```

**Solution avec zone linéaire [0.048, 0.052]** :
```
Algorithme :
1. Trouve point le plus proche de 0.048 → t=0.048s, v=100.2
2. Trouve point le plus proche de 0.052 → t=0.052s, v=101.3
3. Trace droite entre (0.048, 100.2) et (0.052, 101.3)
4. IGNORE complètement les points à 0.049, 0.050, 0.051

Résultat : Pic complètement supprimé, transition lisse
```

### 2. Court-circuiter une zone bruitée

**Situation :**
```
Zone [0.03-0.05] avec beaucoup de bruit haute fréquence
Mais les points aux extrémités sont bons
```

**Solution :**
```
Zone linéaire [0.03, 0.05]
→ Droite entre point à t≈0.03 et point à t≈0.05
→ Tous les points entre = ignorés
→ Zone "nettoyée" instantanément
```

### 3. Créer une rampe forcée

**Situation :**
```
Besoin d'une montée parfaitement linéaire entre t=0.00 et t=0.02
Mais les données mesurées ont des variations
```

**Solution :**
```
Zone linéaire [0.00, 0.02]
→ Trouve valeur au premier point (t≈0.00)
→ Trouve valeur au dernier point (t≈0.02)
→ Rampe parfaitement linéaire
```

### 4. "Sauter" une section problématique

**Situation :**
```
Zone [0.06-0.08] avec données complètement aberrantes
Impossible à corriger avec lissage
```

**Solution :**
```
Zone linéaire [0.06, 0.08]
→ Connecte simplement le point avant avec le point après
→ Section problématique court-circuitée
```

## 🔧 Algorithme détaillé

### Étapes

```python
Pour une zone linéaire [t_start, t_end] :

1. Trouver le point de données le plus proche de t_start :
   idx_start = argmin(|x - t_start|)
   Point A = (x[idx_start], y[idx_start])

2. Trouver le point de données le plus proche de t_end :
   idx_end = argmin(|x - t_end|)
   Point B = (x[idx_end], y[idx_end])

3. Pour tout t dans [t_start, t_end] :
   valeur(t) = interpolation_linéaire(A, B, t)
   
   Formule : y = y_A + (y_B - y_A) * (t - x_A) / (x_B - x_A)

4. Tous les points entre A et B sont IGNORÉS
```

### Avec transitions (1%)

```python
Transition entrante (début de zone) :
- 0% → Méthode globale pure
- 1% → Mélange progressif
- ...
- 99% → Zone linéaire pure

Transition sortante (fin de zone) :
- Même chose en sens inverse
```

## 📊 Comparaisons visuelles

### Exemple 1 : Pic aberrant

**Données brutes :**
```
100 ●
    │    ●450 ← Pic
    │   ╱ ╲
    │  ●   ●
    │ ╱     ╲
    ●───────●
```

**Zone Exacte (PCHIP) :**
```
Passe par le pic → Pic conservé
```

**Zone Linéaire (2 points) :**
```
100 ●─────────●
    │         │
    │  Points │
    │  ignorés│
    ●─────────●
    
Droite entre premier et dernier point
```

### Exemple 2 : Bruit dense

**Données brutes (10 points bruités) :**
```
●╱╲╱╲╱╲╱╲╱╲╱●
 ╲╱ ╲╱ ╲╱ ╲╱
```

**Zone Linéaire :**
```
●━━━━━━━━━━●
  (8 points intermédiaires ignorés)
```

## ⚙️ Interface utilisateur

### Dialogue de création

```
┌─ Définir une zone ──────────────────────────┐
│                                              │
│  Plage de temps (0.0 à 0.125000 s)         │
│                                              │
│  Début (s) : [0.048000]                     │
│  Fin (s)   : [0.052000]                     │
│                                              │
│  ─────────────────────────────────────────── │
│                                              │
│  Type d'interpolation dans la zone :         │
│  ○ Exacte (PCHIP - passe par tous points)  │
│  ● Linéaire (droite entre 2 points - ignore│
│     les points intermédiaires)              │
│                                              │
│  Note : Type 'Linéaire' trace une droite    │
│  entre le premier et dernier point de la    │
│  zone, sautant tous les points              │
│  intermédiaires problématiques.             │
│                                              │
│                        [Annuler]  [  OK  ]   │
└──────────────────────────────────────────────┘
```

### Dans la liste

```
Zones définies :
[0.048000 → 0.052000] Linéaire    ← Supprime pic
[0.080000 → 0.090000] Exacte      ← Conserve détails
```

## 💡 Conseils d'utilisation

### Quand utiliser Zone Linéaire

✅ **Pic isolé aberrant** : Entourez le pic avec la zone  
✅ **Bruit dense** : Zone large sur section bruitée  
✅ **Données manquantes/corrompues** : Court-circuitez  
✅ **Rampe forcée** : Entre deux valeurs stables  

### Quand utiliser Zone Exacte

✅ **Transitoire rapide** : Événement réel à préserver  
✅ **Pic physique** : Pas aberrant mais réel  
✅ **Haute précision** : Besoin des détails  

### Bonnes pratiques

1. **Observer d'abord** : Identifier les points problématiques
2. **Sélectionner les bornes** : Juste avant et après la zone problématique
3. **Vérifier en prévi** : L'effet est visible immédiatement
4. **Ajuster si besoin** : Élargir ou réduire la zone

### Exemple de workflow

```
1. Charger données → Étape 2
2. Observer courbe Q_inlet1 : Pic à t=0.050s
3. Cliquer [⚙️ Zones] Q_inlet1
4. [➕ Ajouter]
5. Début : 0.048
6. Fin : 0.052
7. Type : ● Linéaire
8. [OK]
9. Observer prévisualisation → Pic disparu !
10. Si besoin, ajuster bornes avec [✏️ Modifier]
```

## 🎯 Avantages vs. ancien comportement

### Ancien (Linéaire entre tous points)

```
Zone [0.048-0.052] avec 5 points :
●──●──●──●──●
Lignes droites entre chaque point consécutif
→ Conserve encore le pic (atténué)
```

### Nouveau (Linéaire entre 2 bornes)

```
Zone [0.048-0.052] avec 5 points :
●           ●
 ━━━━━━━━━━
3 points centraux complètement ignorés
→ Pic totalement supprimé
```

**Beaucoup plus efficace pour nettoyer !**

## 📝 Changelog v2.7

### Modifié 🔧
- **Zone Linéaire** : Maintenant interpolation entre seulement les 2 points de borne
- **Algorithme** : Recherche des points les plus proches de t_start et t_end
- **Comportement** : Tous les points intermédiaires sont ignorés

### Ajouté ✨
- **Note explicative** : Dans le dialogue de zone
- **Description claire** : "droite entre 2 points - ignore intermédiaires"

### Documentation 📚
- Guide complet des cas d'usage
- Exemples visuels avant/après
- Comparaison avec Zone Exacte

---

**Maintenant tu peux vraiment "sauter" des sections problématiques de tes courbes !** 🎯
