#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lanceur autonome du generateur de profils Fluent (.prof).

Aucune installation n'est necessaire. Ce script ajoute lui-meme le dossier
``src`` au chemin d'import de Python, puis demarre l'interface graphique.
Le projet n'a donc pas besoin d'etre installe comme module (pas de
``pip install``, pas de ``setup.py``, pas de PYTHONPATH a configurer).

Utilisation :
    python launch.py             demarre l'application
    python launch.py --check     affiche un diagnostic de l'environnement
"""

import os
import sys
import traceback

APP_NAME = "Generateur de profils Fluent"

#: Modules tiers requis, avec le nom du paquet a installer si absent.
REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("matplotlib", "matplotlib"),
]

MIN_PYTHON = (3, 8)


# ---------------------------------------------------------------------
# Localisation du projet
# ---------------------------------------------------------------------

def project_root():
    """Dossier du projet, independant du repertoire courant."""
    try:
        here = os.path.abspath(__file__)
    except NameError:
        # Execution via exec() ou copier-coller dans une console
        here = os.path.abspath(os.path.join(os.getcwd(), "launch.py"))
    return os.path.dirname(here)


def src_dir():
    return os.path.join(project_root(), "src")


def add_src_to_path():
    """
    Rend les paquets du projet importables sans installation.

    Returns:
        Chemin du dossier ``src``

    Raises:
        RuntimeError: si le dossier ``src`` est absent ou incomplet
    """
    src = src_dir()
    if not os.path.isdir(src):
        raise RuntimeError(
            "Dossier 'src' introuvable a cote de launch.py.\n\n"
            "Attendu : {}\n\n"
            "Verifiez que le dossier du projet a ete copie en entier.".format(src)
        )
    missing = [
        name for name in ("core", "gui")
        if not os.path.isdir(os.path.join(src, name))
    ]
    if missing:
        raise RuntimeError(
            "Le dossier 'src' est incomplet : {} manquant(s).\n\n"
            "Recopiez le projet en entier.".format(", ".join(sorted(missing)))
        )

    if src in sys.path:
        sys.path.remove(src)
    sys.path.insert(0, src)
    return src


# ---------------------------------------------------------------------
# Verification de l'environnement
# ---------------------------------------------------------------------

def check_python():
    """Retourne un message d'erreur si la version de Python est trop ancienne."""
    if sys.version_info < MIN_PYTHON:
        return (
            "Python {}.{} ou superieur est requis (version detectee : {}).\n\n"
            "Executable utilise :\n{}".format(
                MIN_PYTHON[0], MIN_PYTHON[1],
                ".".join(str(v) for v in sys.version_info[:3]),
                sys.executable,
            )
        )
    return None


def check_tkinter():
    """Retourne un message d'erreur si tkinter est indisponible."""
    try:
        import tkinter  # noqa: F401
    except Exception as exc:
        return (
            "Le module graphique tkinter n'est pas disponible ({}).\n\n"
            "Sous Windows et avec Anaconda, tkinter est normalement inclus.\n"
            "Sous Linux, installez-le via le gestionnaire de paquets :\n"
            "    sudo apt-get install python3-tk".format(exc)
        )
    return None


def missing_packages():
    """Liste des modules tiers requis qui ne sont pas importables."""
    missing = []
    for module_name, package_name in REQUIRED_PACKAGES:
        try:
            __import__(module_name)
        except Exception:
            missing.append(package_name)
    return missing


def configure_matplotlib():
    """
    Force le backend Tk de matplotlib.

    Utile sous Anaconda et Spyder, ou le backend par defaut peut etre Qt ou
    un backend "inline" incompatible avec l'integration dans tkinter.
    """
    try:
        import matplotlib
        matplotlib.use("TkAgg", force=True)
    except Exception:
        # Non bloquant : l'application n'utilise pas pyplot
        pass


def verify_project_imports(src):
    """
    Verifie que les paquets 'core' et 'gui' seraient bien charges depuis le
    projet, et non depuis un autre paquet de l'environnement portant le meme
    nom. La verification n'execute pas les modules.
    """
    import importlib.util

    src_real = os.path.realpath(src)
    for name in ("core", "gui"):
        try:
            spec = importlib.util.find_spec(name)
        except Exception:
            spec = None
        origin = getattr(spec, "origin", None) if spec else None
        if not origin:
            raise RuntimeError(
                "Le paquet '{}' du projet est introuvable dans :\n{}".format(
                    name, src_real
                )
            )
        if not os.path.realpath(origin).startswith(src_real):
            raise RuntimeError(
                "Le module '{}' serait charge depuis :\n{}\n\n"
                "au lieu du dossier du projet :\n{}\n\n"
                "Un autre paquet de l'environnement porte le meme nom. "
                "Lancez l'application depuis le dossier du projet.".format(
                    name, origin, src_real
                )
            )


# ---------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------

def run_check():
    """Affiche un rapport de diagnostic sur la sortie standard."""
    lines = []
    lines.append("=" * 62)
    lines.append(" Diagnostic - " + APP_NAME)
    lines.append("=" * 62)
    lines.append("")
    lines.append("Python      : {}".format(sys.version.split()[0]))
    lines.append("Executable  : {}".format(sys.executable))
    lines.append("Projet      : {}".format(project_root()))
    lines.append("Dossier src : {}".format(src_dir()))
    lines.append("")

    problem = check_python()
    lines.append("Version de Python : {}".format("OK" if problem is None else "PROBLEME"))
    if problem:
        lines.append("    " + problem.replace("\n", "\n    "))

    problem = check_tkinter()
    lines.append("tkinter           : {}".format("OK" if problem is None else "ABSENT"))
    if problem:
        lines.append("    " + problem.replace("\n", "\n    "))

    lines.append("")
    lines.append("Modules requis :")
    for module_name, package_name in REQUIRED_PACKAGES:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "?")
            location = os.path.dirname(getattr(module, "__file__", "") or "")
            lines.append("    {:<12} OK      {:<10} {}".format(module_name, version, location))
        except Exception as exc:
            lines.append("    {:<12} ABSENT  ({})".format(module_name, exc))

    lines.append("")
    try:
        src = add_src_to_path()
        verify_project_imports(src)
        lines.append("Modules du projet : OK (importes depuis le dossier du projet)")
    except Exception as exc:
        lines.append("Modules du projet : PROBLEME")
        lines.append("    " + str(exc).replace("\n", "\n    "))

    lines.append("")
    lines.append("Aucune installation n'est requise : lancez 'python launch.py'.")
    lines.append("=" * 62)
    print("\n".join(lines))


# ---------------------------------------------------------------------
# Rapport d'erreur
# ---------------------------------------------------------------------

def has_console():
    """Vrai si un terminal est attache (les messages y seront visibles)."""
    try:
        return sys.stderr is not None and sys.stderr.isatty()
    except Exception:
        return False


def show_error(title, message, detail=None):
    """
    Signale une erreur a l'utilisateur.

    Ecrit sur la sortie d'erreur et, si possible, ouvre une fenetre : sans
    cela un double-clic sur launch.py fermerait la console avant lecture.
    """
    text = message if detail is None else message + "\n\n" + detail
    sys.stderr.write("\n" + title + "\n" + text + "\n")

    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title(title)
        root.geometry("760x440")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame, text=message, wraplength=720, justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 10))

        if detail:
            box = tk.Text(frame, wrap="word", height=14, font=("Consolas", 9))
            scroll = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
            box.configure(yscrollcommand=scroll.set)
            box.insert("1.0", detail)
            box.configure(state="disabled")
            box.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

        ttk.Button(root, text="Fermer", command=root.destroy).pack(pady=8)
        root.mainloop()
    except Exception:
        # tkinter indisponible : le message sur stderr suffit
        if not has_console():
            try:
                log = os.path.join(project_root(), "L1DMaker_erreur.log")
                with open(log, "w", encoding="utf-8") as handle:
                    handle.write(title + "\n" + text + "\n")
            except Exception:
                pass


# ---------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if "--check" in argv or "-c" in argv:
        run_check()
        return 0

    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    problem = check_python()
    if problem:
        show_error("Version de Python incompatible", problem)
        return 1

    problem = check_tkinter()
    if problem:
        show_error("Interface graphique indisponible", problem)
        return 1

    absent = missing_packages()
    if absent:
        show_error(
            "Modules manquants",
            "Les modules suivants sont requis mais introuvables :\n    {}\n\n"
            "Avec Anaconda, ils sont normalement deja presents. Verifiez que "
            "vous lancez l'application avec le Python d'Anaconda :\n{}\n\n"
            "Lancez 'python launch.py --check' pour un diagnostic complet.".format(
                ", ".join(absent), sys.executable
            ),
        )
        return 1

    try:
        src = add_src_to_path()
        configure_matplotlib()
        verify_project_imports(src)
        from gui.app import run
    except RuntimeError as exc:
        show_error("Projet introuvable ou incomplet", str(exc))
        return 1
    except Exception:
        show_error(
            "Erreur au chargement de l'application",
            "L'application n'a pas pu etre chargee depuis :\n{}".format(src_dir()),
            traceback.format_exc(),
        )
        return 1

    try:
        run()
    except Exception:
        show_error(
            "Erreur pendant l'execution",
            "L'application s'est interrompue de facon inattendue.",
            traceback.format_exc(),
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
