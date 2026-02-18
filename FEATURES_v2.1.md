# Nouvelles fonctionnalités v2.1

## 🎯 Améliorations apportées

### 1. Choix de la méthode d'interpolation

Vous pouvez maintenant choisir entre **deux méthodes d'interpolation** pour chaque type de données (Q et T) :

#### **PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)**
- ✅ **Interpolation exacte** : passe par tous les points de données
- ✅ **Préserve la monotonie** : pas d'oscillations non physiques entre les points
- ✅ **Dérivées continues** : garantit une courbe lisse sans sauts de pente
- ⚠️ **Pas de lissage** : reproduit fidèlement toutes les variations des données brutes

**Quand utiliser PCHIP ?**
- Données de bonne qualité avec peu de bruit
- Besoin de reproduire exactement les variations mesurées
- Préférence pour une interpolation conservative sans modification des données

#### **Spline lissée (UnivariateSpline)**
- ✅ **Lissage ajustable** : paramètre de lissage de 0 (exact) à 0.1 (très lissé)
- ✅ **Réduit le bruit** : filtre les variations haute fréquence
- ✅ **Contrôle des dérivées** : évite les gradients trop importants
- 📊 **Facteur de lissage** : `s = n × (smooth_factor × range)²`

**Quand utiliser Spline lissée ?**
- Données bruitées nécessitant un filtrage
- Besoin de contrôler les dérivées pour éviter les divergences CFD
- Données avec quelques points aberrants

### 2. Visualisation améliorée avec lignes linéaires

Chaque graphique affiche maintenant **3 courbes** :

1. **Lignes linéaires grises** (référence)
   - Interpolation linéaire simple entre les points
   - Sert de référence pour comparer
   - Couleur : gris clair, fin, semi-transparent

2. **Points de données brutes** (cercles)
   - Points d'origine du fichier CSV
   - Taille : plus gros pour meilleure visibilité
   - Toujours au-dessus des autres courbes

3. **Courbe interpolée** (ligne colorée)
   - Résultat de la méthode choisie (PCHIP ou Spline)
   - Épaisseur : plus épaisse pour ressortir
   - Affiche le nom de la méthode et les paramètres dans la légende

**Avantages de cette visualisation :**
- ✅ Facilite la comparaison entre interpolation simple et avancée
- ✅ Permet de voir l'effet du lissage par rapport à du linéaire
- ✅ Met en évidence les zones où l'interpolation diffère significativement

### 3. Interface utilisateur adaptative

#### Activation/désactivation intelligente
- Quand **PCHIP** est sélectionné :
  - ❌ Le slider de lissage est **désactivé** (grisé)
  - ℹ️ Message : "PCHIP = interpolation exacte (pas de lissage disponible)"
  
- Quand **Spline** est sélectionnée :
  - ✅ Le slider de lissage est **activé**
  - ℹ️ Indications : "0 = exacte | 0.001-0.01 = léger | >0.01 = fort"

#### Informations dans la prévisualisation finale
L'étape 3 affiche maintenant :
- Méthode Q utilisée (pchip ou spline)
- Méthode T utilisée (pchip ou spline)
- Facteurs de lissage pour Q et T

## 📊 Exemples d'utilisation

### Cas 1 : Données de bonne qualité
**Configuration recommandée :**
- Méthode Q : **PCHIP**
- Méthode T : **PCHIP**

**Résultat :** Reproduction fidèle des données sans modification

### Cas 2 : Débits bruités, températures lisses
**Configuration recommandée :**
- Méthode Q : **Spline** avec lissage = 0.005
- Méthode T : **PCHIP**

**Résultat :** Débits lissés, températures exactes

### Cas 3 : Tout lisser pour éviter divergences
**Configuration recommandée :**
- Méthode Q : **Spline** avec lissage = 0.01
- Méthode T : **Spline** avec lissage = 0.02

**Résultat :** Courbes très lisses avec gradients modérés

### Cas 4 : Comparaison visuelle
1. Sélectionner **PCHIP** pour les deux
2. Observer la différence avec l'interpolation linéaire (lignes grises)
3. Si trop de variations, passer en **Spline** et ajuster le lissage
4. Comparer en temps réel l'effet

## 🎨 Légende des graphiques

Dans chaque graphique, vous verrez :

```
━━━ Interpolation linéaire (référence)  [gris clair, fin]
●●● Données brutes                       [points]
━━━ PCHIP (interpolation exacte)        [ligne colorée épaisse]
    ou
━━━ Spline lissée (s=0.0050)            [ligne colorée épaisse]
```

## 💡 Conseils d'utilisation

1. **Commencez par PCHIP** pour voir les données telles quelles
2. **Comparez avec les lignes linéaires** pour identifier les zones problématiques
3. Si les gradients semblent trop forts, **passez en Spline** et augmentez progressivement le lissage
4. **Utilisez la prévisualisation temps réel** pour trouver le bon compromis
5. **Naviguez librement** entre les étapes pour ajuster les paramètres

## 🔄 Navigation flexible conservée

Toutes les fonctionnalités de navigation restent actives :
- ✅ Retour arrière possible à tout moment
- ✅ Conservation des paramètres (méthodes, lissage, fichiers)
- ✅ Widgets réutilisés pour éviter les rechargements
- ✅ Prévisualisation temps réel maintenue

## 📝 Notes techniques

### Ordre d'affichage (zorder)
Pour une lisibilité optimale :
1. **zorder=1** : Lignes linéaires (en arrière-plan)
2. **zorder=2** : Courbe interpolée (au milieu)
3. **zorder=3** : Points bruts (au premier plan)

### Épaisseurs de ligne
- Linéaire : 0.8-1.0 px (fin)
- Interpolée : 1.5-2.0 px (moyen)
- Points : 4-6 px de diamètre

### Transparence
- Lignes linéaires : alpha=0.4-0.5 (semi-transparent)
- Points bruts : alpha=0.7-0.9 (opaque)
- Courbe interpolée : alpha=1.0 (totalement opaque)

## 🚀 Comment tester

```bash
# Lancer l'application
./run.sh  # Linux/Mac
run.bat   # Windows

# Workflow suggéré pour tester
1. Charger vos 4 fichiers CSV (étape 1)
2. À l'étape 2, essayer PCHIP sur tout
3. Observer les lignes linéaires vs PCHIP
4. Changer Q en Spline, ajuster le lissage
5. Comparer visuellement
6. Valider dans la prévisualisation finale
```

## 📈 Avant / Après

### Avant v2.1
- ❌ Une seule méthode (Spline)
- ❌ Pas de référence visuelle
- ❌ Difficile de juger l'effet du lissage

### Après v2.1
- ✅ Deux méthodes au choix (PCHIP + Spline)
- ✅ Lignes linéaires de référence
- ✅ Comparaison visuelle immédiate
- ✅ UI adaptative selon la méthode
- ✅ Information complète à l'étape 3
