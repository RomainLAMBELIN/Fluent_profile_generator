#!/bin/bash
# Lancement du generateur de profils Fluent sous Linux/Mac.
# Aucune installation n'est necessaire.

cd "$(dirname "$0")" || exit 1

echo "Démarrage du générateur de profils Fluent..."

if command -v python3 >/dev/null 2>&1; then
    exec python3 launch.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python launch.py "$@"
else
    echo "ERREUR : aucun interpréteur Python trouvé." >&2
    echo "Installez Python 3.8+ ou activez votre environnement Anaconda." >&2
    exit 1
fi
