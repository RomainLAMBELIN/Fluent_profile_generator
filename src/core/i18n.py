"""
Internationalisation de l'interface : français (par défaut) et anglais.

Les chaînes sources sont en français : la langue par défaut ne nécessite
aucune table, et le code reste lisible sans passer par des identifiants
abstraits. Une traduction manquante retombe silencieusement sur le
français plutôt que d'afficher une clé technique à l'utilisateur.

Usage :
    from core.i18n import t
    ttk.Label(parent, text=t("Fichier CSV :"))
    label = t("Étape {n} / {total}", n=1, total=4)
"""

DEFAULT_LANGUAGE = "fr"

#: Codes de langue et libellés affichés dans le sélecteur
LANGUAGES = {
    "fr": "Français",
    "en": "English",
}


_ENGLISH = {
    # -- Fenêtre principale et navigation ------------------------------
    "Générateur de profils Fluent (.prof)": "Fluent Profile Generator (.prof)",
    "Langue :": "Language:",
    "Étape {n} : {title}": "Step {n}: {title}",
    "Étape {n} / {total}": "Step {n} of {total}",
    "← Précédent": "← Previous",
    "Suivant →": "Next →",
    "Terminer": "Finish",
    "Quitter": "Quit",
    "Voulez-vous vraiment quitter ?": "Do you really want to quit?",
    "Validation": "Validation",
    "Erreur": "Error",
    "Erreur lors du chargement :\n\n{error}": "Error while loading:\n\n{error}",
    "Erreur lors de l'interpolation :\n\n{error}": "Error during interpolation:\n\n{error}",

    # -- Titres des étapes ---------------------------------------------
    "Import du fichier CSV": "CSV file import",
    "Importez un fichier CSV multi-colonnes et configurez le mapping des inlets":
        "Import a multi-column CSV file and map its columns to each inlet",
    "Paramètres d'interpolation": "Interpolation settings",
    "Ajustez les paramètres et observez l'effet sur les courbes":
        "Adjust the settings and watch their effect on the curves",
    "Prévisualisation finale": "Final preview",
    "Vérifiez les courbes interpolées avant l'export":
        "Check the interpolated curves before exporting",
    "Export du fichier .prof": "Export the .prof file",
    "Enregistrez le profil Fluent": "Save the Fluent profile",

    # -- Étape 1 : import ----------------------------------------------
    "Importez un fichier CSV multi-colonnes avec header.\n"
    "Les colonnes seront auto-détectées et vous pourrez configurer le mapping.":
        "Import a multi-column CSV file with a header row.\n"
        "Columns are detected automatically and you can adjust the mapping.",
    "Fichier CSV :": "CSV file:",
    "Parcourir...": "Browse...",
    "Aperçu du fichier CSV :": "CSV file preview:",
    "Mapping des colonnes :": "Column mapping:",
    "Colonne temps :": "Time column:",
    "+ Ajouter un inlet": "+ Add an inlet",
    "Aucun fichier chargé": "No file loaded",
    "Sélectionner le fichier CSV": "Select the CSV file",
    "Erreur de lecture : {error}": "Read error: {error}",
    "Inlet {n}": "Inlet {n}",
    "Colonne Q :": "Q column:",
    "Colonne T :": "T column:",
    "Nom export :": "Export name:",
    "X Supprimer": "X Remove",
    "{n} inlet(s) configuré(s)": "{n} inlet(s) configured",
    "  —  {n} paires Q/T reconnues dans le fichier, "
    "« + Ajouter un inlet » complète avec les suivantes":
        "  —  {n} Q/T pairs found in the file; "
        "“+ Add an inlet” fills in the next ones",
    "Veuillez sélectionner un fichier CSV.": "Please select a CSV file.",
    "Veuillez sélectionner la colonne de temps.": "Please select the time column.",
    "Inlet {n} : colonne Q non sélectionnée.": "Inlet {n}: no Q column selected.",
    "Inlet {n} : colonne T non sélectionnée.": "Inlet {n}: no T column selected.",
    "Aucun inlet configuré.": "No inlet configured.",
    "La colonne '{col}' est utilisée plusieurs fois.":
        "Column '{col}' is used more than once.",

    # -- Étape 2 : paramétrage -----------------------------------------
    "Chargement...": "Loading...",
    "Chargement des paramètres...": "Loading settings...",
    "Paramètres globaux": "Global settings",
    "Pas de temps (µs) :": "Time step (µs):",
    "Remplacement débits nuls :": "Zero-flow replacement:",
    "Afficher les dérivées (pentes)": "Show derivatives (slopes)",
    "? Aide sur les méthodes et les zones": "? Help on methods and zones",
    "Rafraîchir prévisualisations": "Refresh previews",
    "Méthode :": "Method:",
    "Lissage :": "Smoothing:",
    "Lambda :": "Lambda:",
    "Inverser la courbe (×-1)": "Invert the curve (×-1)",
    "Zones": "Zones",
    "0 zone": "0 zone",
    "{n} zone(s)": "{n} zone(s)",
    "Durée simulation : {duration} s  |  Pas de temps : {dt} s ({dt_us} µs)  |  "
    "Points interpolés : {points}  |  Zones définies : {zones}":
        "Simulation duration: {duration} s  |  Time step: {dt} s ({dt_us} µs)  |  "
        "Interpolated points: {points}  |  Zones defined: {zones}",
    "Le pas de temps doit être > 0": "The time step must be > 0",
    "FLOW_EPS doit être > 0": "FLOW_EPS must be > 0",
    "Erreur : {error}": "Error: {error}",

    # -- Graphiques ----------------------------------------------------
    "Temps (s)": "Time (s)",
    "Valeur": "Value",
    "Linéaire": "Linear",
    "Brut": "Raw",
    "Traité": "Processed",
    "Mesures": "Measurements",
    "Débit": "Flow rate",
    "Température": "Temperature",
    "Débit {name} (Q)": "Flow rate {name} (Q)",
    "Température {name} (T)": "Temperature {name} (T)",

    # -- Analyse des pentes --------------------------------------------
    "Pente (unité/s)": "Slope (unit/s)",
    "Pente (unité/s)\néchelle log sym.": "Slope (unit/s)\nsymlog scale",
    "Pente max": "Max slope",
    "brute": "raw",
    "traitée": "processed",
    "indisponible": "unavailable",
    "à t = {time} s": "at t = {time} s",
    "Variations réduites de {percent} %": "Variations reduced by {percent} %",
    "Variations accrues de {percent} %": "Variations increased by {percent} %",
    "Variations quasi inchangées": "Variations nearly unchanged",
    "Pente max : {raw} → {processed} /s": "Max slope: {raw} → {processed} /s",
    "Erreur: {percent}% (abs: {absolute})": "Error: {percent}% (abs: {absolute})",
    "Erreur abs: {absolute}": "Abs. error: {absolute}",

    # -- Étape 3 : prévisualisation ------------------------------------
    "Aucune donnée interpolée disponible": "No interpolated data available",
    "Durée : {duration} s  |  Pas de temps : {dt} s  |  Points : {points}  |  "
    "Zones totales : {zones}":
        "Duration: {duration} s  |  Time step: {dt} s  |  Points: {points}  |  "
        "Total zones: {zones}",

    # -- Étape 4 : export ----------------------------------------------
    "Prêt à exporter le fichier .prof": "Ready to export the .prof file",
    "Cliquez sur 'Exporter' pour sauvegarder le profil Fluent":
        "Click “Export” to save the Fluent profile",
    "📁 Exporter vers .prof...": "📁 Export to .prof...",
    "Enregistrer le fichier .prof": "Save the .prof file",
    "Profil Fluent": "Fluent profile",
    "Tous fichiers": "All files",
    "Export terminé": "Export complete",
    "✅ Export réussi !\n\n{path}\n\n{columns} colonnes × {points} points":
        "✅ Export successful\n\n{path}\n\n{columns} columns × {points} points",
    "Le fichier .prof a été créé avec succès :\n\n{path}\n\n"
    "{columns} colonnes × {points} points":
        "The .prof file was created successfully:\n\n{path}\n\n"
        "{columns} columns × {points} points",
    "❌ Erreur lors de l'export :\n\n{error}": "❌ Export error:\n\n{error}",
    "Erreur lors de l'export :\n\n{error}": "Export error:\n\n{error}",

    # -- Dialogue des zones --------------------------------------------
    "Zones spéciales - {variable} {name}": "Special zones - {variable} {name}",
    "Cliquez-glissez sur le graphique pour sélectionner une plage, ou saisissez "
    "les bornes. Les bornes sont ajustées aux points de mesure les plus proches. "
    "Méthode globale : {method}. Données : {start} → {end} s ({points} points).":
        "Click and drag on the chart to select a range, or type the bounds. "
        "Bounds snap to the nearest measurement points. "
        "Global method: {method}. Data: {start} → {end} s ({points} points).",
    "Zones définies": "Defined zones",
    "Début (s)": "Start (s)",
    "Fin (s)": "End (s)",
    "Type": "Type",
    "Points": "Points",
    "Exacte": "Exact",
    "Supprimer": "Remove",
    "Tout supprimer": "Remove all",
    "Supprimer toutes les zones ?": "Remove every zone?",
    "Confirmer": "Confirm",
    "Zone en cours d'édition": "Zone being edited",
    "Début (s) :": "Start (s):",
    "Fin (s) :": "End (s):",
    "Type :": "Type:",
    "Exacte (PCHIP par tous les points)": "Exact (PCHIP through every point)",
    "Linéaire (droite entre les bornes)": "Linear (straight line between bounds)",
    "Aucune plage sélectionnée.": "No range selected.",
    "Plage ajustée : {start} → {end} s ({points} points de mesure)":
        "Snapped range: {start} → {end} s ({points} measurement points)",
    "Bornes invalides : saisir deux nombres.": "Invalid bounds: enter two numbers.",
    "La zone doit contenir au moins 2 points de mesure.":
        "A zone must contain at least 2 measurement points.",
    "Ajouter": "Add",
    "Appliquer": "Apply",
    "Nouvelle": "New",
    "Vert : zone exacte · Violet : zone linéaire · Rouge hachuré : zone en édition.\n"
    "Les zones ne peuvent pas se chevaucher (elles peuvent se toucher).\n"
    "Le raccord avec le reste de la courbe est continu.":
        "Green: exact zone · Purple: linear zone · Red hatching: zone being edited.\n"
        "Zones cannot overlap (they may touch).\n"
        "The junction with the rest of the curve is continuous.",
    "Prévisualisation": "Preview",
    "Chevauchement": "Overlap",
    "La plage chevauche la zone {n} [{start} → {end}].":
        "The range overlaps zone {n} [{start} → {end}].",
    "Zone": "Zone",
    "Définissez d'abord une plage : cliquez-glissez sur le graphique ou "
    "saisissez les bornes.":
        "Define a range first: click and drag on the chart, or type the bounds.",
    "Sans zone": "Without zones",
    "Avec {n} zone(s)": "With {n} zone(s)",
    "Aperçu avec la zone en édition": "Preview with the zone being edited",
    "Sans zone : {error}": "Without zones: {error}",
    "Avec zones : {error}": "With zones: {error}",
    "{n} zone(s) définie(s)": "{n} zone(s) defined",
    "Erreur : ": "Error: ",
    "référence : {error}": "reference: {error}",
    "zones : {error}": "zones: {error}",
    "aperçu : {error}": "preview: {error}",
    "Annuler": "Cancel",

    # -- Méthodes d'interpolation (libellés des menus) ------------------
    "Spline lissée": "Smoothed spline",

    # -- Aide ----------------------------------------------------------
    "Aide - Méthodes d'interpolation": "Help - Interpolation methods",
    "Guide des méthodes d'interpolation": "Guide to interpolation methods",
    "Fermer": "Close",
    "MÉTHODES D'INTERPOLATION": "INTERPOLATION METHODS",
    "ZONES SPÉCIALES": "SPECIAL ZONES",
    "LECTURE DES DÉRIVÉES (PENTES)": "READING THE DERIVATIVES (SLOPES)",
    "RECOMMANDATIONS CFD": "CFD RECOMMENDATIONS",
}


# Textes longs de l'aide. Les clés reprennent les sources exactes du code.
_ENGLISH.update({
    "PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)\n\nInterpolation exacte qui passe par tous les points de données.\nPréserve la monotonie locale (pas d'oscillations entre points).\n\nAvantages : Exacte, stable, préserve la monotonie\nInconvénients : Peut amplifier le bruit si données bruitées\n\nRecommandé pour : Données propres et précises":
        'PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)\n\nExact interpolation passing through every data point.\nPreserves local monotonicity (no oscillation between points).\n\nPros: Exact, stable, preserves monotonicity\nCons: Can amplify noise on noisy data\n\nRecommended for: Clean, accurate data',
    'Spline Cubique Lissée\n\nSpline cubique avec paramètre de lissage ajustable.\nNe passe pas exactement par les points (compromis fidélité/lissage).\n\nAvantages : Contrôle fin du lissage\nInconvénients : Peut osciller aux extrémités\n\nParamètre : Plus le facteur est grand, plus la courbe est lissée.\nRecommandé pour : Données légèrement bruitées':
        'Smoothed Cubic Spline\n\nCubic spline with an adjustable smoothing parameter.\nDoes not pass exactly through the points (fidelity/smoothness trade-off).\n\nPros: Fine control over smoothing\nCons: Can oscillate near the ends\n\nParameter: The larger the factor, the smoother the curve.\nRecommended for: Slightly noisy data',
    'Trend Filter L2 (Ridge / HP Filter)\n\nMinimise : ||données - résultat||² + lambda ||courbure||²\n\nProduit une courbe globalement lissée en pénalisant les courbures.\nTrès efficace pour réduire les variations "violentes".\n\nAvantages : Réduit oscillations, stable numériquement\nInconvénients : Peut trop lisser les détails fins\n\nParamètre lambda : Plus grand = plus lisse (typique: 1-50)\nRecommandé pour : Simulations CFD, conditions aux limites':
        'Trend Filter L2 (Ridge / HP Filter)\n\nMinimises: ||data - result||² + lambda ||curvature||²\n\nProduces a globally smooth curve by penalising curvature.\nVery effective at reducing violent variations.\n\nPros: Reduces oscillation, numerically stable\nCons: Can over-smooth fine detail\n\nLambda parameter: Larger = smoother (typical: 1-50)\nRecommended for: CFD simulations, boundary conditions',
    'Trend Filter L1 (Total Variation)\n\nMinimise : ||données - résultat||² + lambda ||courbure||_1\n\nProduit une courbe simplifiée avec segments de courbure constante.\nPréserve mieux les changements brusques légitimes.\n\nAvantages : Très robuste au bruit, préserve les transitions\nInconvénients : Peut créer des "plateaux"\n\nParamètre lambda : Plus grand = plus simple (typique: 1-20)\nRecommandé pour : Données très bruitées avec transitions nettes':
        'Trend Filter L1 (Total Variation)\n\nMinimises: ||data - result||² + lambda ||curvature||_1\n\nProduces a simplified curve made of constant-curvature segments.\nPreserves genuine abrupt changes better.\n\nPros: Very robust to noise, preserves transitions\nCons: Can create plateaus\n\nLambda parameter: Larger = simpler (typical: 1-20)\nRecommended for: Very noisy data with sharp transitions',
    "Interpolation Linéaire\n\nSegments de droites entre chaque paire de points consécutifs.\nLa méthode la plus simple et la plus rapide.\n\nAvantages : Simple, rapide, pas d'oscillations\nInconvénients : Discontinuités de pente aux points\n\nRecommandé pour : Validation rapide, données peu nombreuses":
        'Linear Interpolation\n\nStraight segments between each pair of consecutive points.\nThe simplest and fastest method.\n\nPros: Simple, fast, no oscillation\nCons: Slope discontinuities at the points\n\nRecommended for: Quick checks, sparse data',
    'Les zones spéciales permettent de définir des régions où l\'interpolation\nest différente du reste de la courbe.\n\nZone "Exacte" (PCHIP)\n   Utilise PCHIP dans cette zone, passant exactement par les points.\n   Utile pour préserver des variations importantes.\n\nZone "Linéaire"\n   Trace une droite entre le premier et dernier point de la zone.\n   Ignore les points intermédiaires.\n   Utile pour simplifier une région ou créer une rampe.\n\nLes bornes d\'une zone sont ajustées aux points de mesure les plus\nproches. Le raccord entre une zone et le reste de la courbe est\ncontinu (la courbe lissée passe par la valeur mesurée à la frontière).\n\n':
        'Special zones let you define regions where the interpolation\ndiffers from the rest of the curve.\n\n"Exact" zone (PCHIP)\n   Uses PCHIP inside the zone, passing exactly through the points.\n   Useful to preserve significant variations.\n\n"Linear" zone\n   Draws a straight line between the first and last point of the zone.\n   Ignores the intermediate points.\n   Useful to simplify a region or to create a ramp.\n\nThe bounds of a zone snap to the nearest measurement points. The\njunction between a zone and the rest of the curve is continuous (the\nsmoothed curve passes through the measured value at the boundary).\n\n',
    "Le panneau du bas compare la pente des données brutes à celle de la\ncourbe traitée. C'est la mesure directe de l'effet du lissage.\n\nPourquoi c'est important\n   Les variations brusques d'une condition aux limites sont la cause\n   principale de divergence dans Fluent. Diviser la pente maximale par\n   dix est un bon indicateur de stabilité du calcul.\n\nCe qui est tracé\n   Bleu en escalier : pente entre deux points de mesure consécutifs.\n   Orange : pente de la courbe interpolée.\n   Losange et trait pointillé : instant où la pente est maximale.\n   Encadré : valeurs chiffrées, instants, et pourcentage de réduction.\n\nÉchelle verticale\n   Quand un pic isolé écrase tout le reste, l'échelle passe\n   automatiquement en logarithmique symétrique afin de montrer à la fois\n   ce pic et la structure fine des variations.\n\nUne réduction affichée en rouge signale une courbe rendue plus raide\nque les données d'origine : à éviter pour un calcul CFD.\n\n":
        'The lower panel compares the slope of the raw data with that of the\nprocessed curve. It measures the effect of the smoothing directly.\n\nWhy it matters\n   Abrupt variations in a boundary condition are the main cause of\n   divergence in Fluent. Dividing the maximum slope by ten is a good\n   indicator of a stable computation.\n\nWhat is plotted\n   Blue steps: slope between two consecutive measurement points.\n   Orange: slope of the interpolated curve.\n   Diamond and dotted line: instant where the slope is largest.\n   Box: figures, instants, and the reduction percentage.\n\nVertical scale\n   When an isolated peak dwarfs everything else, the scale switches\n   automatically to symmetric logarithmic so that both the peak and the\n   fine structure of the variations remain visible.\n\nA reduction shown in red means the curve was made steeper than the\noriginal data: to be avoided for a CFD computation.\n\n',
    'Pour les simulations CFD (Ansys Fluent), les variations brusques\naux conditions aux limites peuvent causer des divergences.\n\nRecommandations :\n1. Commencer avec Trend Filter L2, lambda = 1 a 5\n2. Si divergence, augmenter lambda (10, 20, 50...)\n3. Pour données très bruitées : Trend Filter L1\n4. Vérifier visuellement que les transitions sont douces\n':
        'For CFD simulations (Ansys Fluent), abrupt variations in the\nboundary conditions can cause divergence.\n\nRecommendations:\n1. Start with Trend Filter L2, lambda = 1 to 5\n2. If it diverges, increase lambda (10, 20, 50...)\n3. For very noisy data: Trend Filter L1\n4. Check visually that the transitions are smooth\n',
})


_TABLES = {"en": _ENGLISH}
_current_language = DEFAULT_LANGUAGE


def available_languages():
    """Dict {code: libellé affiché} des langues disponibles."""
    return dict(LANGUAGES)


def get_language():
    """Code de la langue courante."""
    return _current_language


def set_language(code):
    """
    Change la langue courante.

    Un code inconnu retombe sur la langue par défaut, afin qu'une
    configuration périmée ne bloque pas le démarrage.
    """
    global _current_language
    _current_language = code if code in LANGUAGES else DEFAULT_LANGUAGE
    return _current_language


def language_display(code):
    """Libellé affiché d'un code de langue."""
    return LANGUAGES.get(code, LANGUAGES[DEFAULT_LANGUAGE])


def language_code(display):
    """Code correspondant à un libellé affiché."""
    for code, name in LANGUAGES.items():
        if name == display:
            return code
    return DEFAULT_LANGUAGE


def t(text, **kwargs):
    """
    Traduit une chaîne source française dans la langue courante.

    Args:
        text: Chaîne source, en français
        **kwargs: Valeurs des champs nommés éventuels

    Returns:
        Chaîne traduite, ou la chaîne source si aucune traduction n'existe
    """
    table = _TABLES.get(_current_language)
    translated = table.get(text, text) if table else text
    if kwargs:
        try:
            return translated.format(**kwargs)
        except (KeyError, IndexError):
            # Une traduction au champ erroné ne doit pas casser l'interface
            return text.format(**kwargs)
    return translated
