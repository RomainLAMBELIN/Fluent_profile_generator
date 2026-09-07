"""
Tests de l'internationalisation.

Le risque principal n'est pas l'absence de traduction, qui retombe sur le
français, mais une traduction dont les champs de substitution divergent de
la source : elle casserait l'affichage à l'exécution.
"""

import json
import re

import pytest

from core.constants import INTERP_METHODS, generate_file_labels
from core.i18n import (
    DEFAULT_LANGUAGE, LANGUAGES, _ENGLISH, t, set_language, get_language,
    available_languages, language_display, language_code,
)

FIELD = re.compile(r"\{(\w+)\}")


@pytest.fixture(autouse=True)
def restore_language():
    """Chaque test repart de la langue par défaut."""
    yield
    set_language(DEFAULT_LANGUAGE)


def test_default_language_is_french():
    assert DEFAULT_LANGUAGE == "fr"
    assert get_language() == "fr"
    assert t("Fichier CSV :") == "Fichier CSV :"


def test_switching_language():
    set_language("en")
    assert get_language() == "en"
    assert t("Fichier CSV :") == "CSV file:"
    set_language("fr")
    assert t("Fichier CSV :") == "Fichier CSV :"


def test_unknown_language_falls_back_to_default():
    assert set_language("de") == DEFAULT_LANGUAGE
    assert set_language(None) == DEFAULT_LANGUAGE
    assert get_language() == DEFAULT_LANGUAGE


def test_missing_translation_returns_the_source():
    set_language("en")
    assert t("Chaîne jamais traduite") == "Chaîne jamais traduite"


def test_formatting_in_both_languages():
    assert t("Étape {n} / {total}", n=2, total=4) == "Étape 2 / 4"
    set_language("en")
    assert t("Étape {n} / {total}", n=2, total=4) == "Step 2 of 4"


def test_formatting_of_untranslated_string():
    set_language("en")
    assert t("Valeur inconnue : {x}", x=3) == "Valeur inconnue : 3"


@pytest.mark.parametrize("source,translated", sorted(_ENGLISH.items()))
def test_placeholders_are_preserved(source, translated):
    """Un champ absent ou renommé provoquerait une erreur à l'affichage."""
    assert set(FIELD.findall(source)) == set(FIELD.findall(translated))


def test_no_empty_translation():
    empty = [src for src, dst in _ENGLISH.items() if not dst.strip()]
    assert empty == []


def test_language_display_and_code_round_trip():
    for code, display in LANGUAGES.items():
        assert language_display(code) == display
        assert language_code(display) == code
    assert language_code("inconnu") == DEFAULT_LANGUAGE
    assert language_display("xx") == LANGUAGES[DEFAULT_LANGUAGE]
    assert available_languages() == LANGUAGES
    # Une copie : modifier le retour ne doit pas altérer la table
    available_languages()["fr"] = "modifié"
    assert LANGUAGES["fr"] == "Français"


@pytest.mark.parametrize("code", sorted(LANGUAGES))
def test_method_labels_stay_unique(code):
    """
    Les libellés servent de valeurs au menu déroulant des méthodes : deux
    méthodes portant le même libellé rendraient la sélection ambiguë.
    """
    set_language(code)
    labels = [t(label) for label in INTERP_METHODS.values()]
    assert len(set(labels)) == len(labels)
    assert all(label.strip() for label in labels)


def test_curve_labels_are_translatable():
    labels = generate_file_labels({1: "tulipe"})
    assert labels["Q_inlet1"] == "Débit tulipe (Q)"

    set_language("en")
    labels = generate_file_labels(
        {1: "tulipe"}, translate=lambda template, name: t(template, name=name)
    )
    assert labels["Q_inlet1"] == "Flow rate tulipe (Q)"
    assert labels["T_inlet1"] == "Temperature tulipe (T)"


def test_error_text_follows_language():
    from core.analysis import format_error_text
    error = {"relative_error_percent": 1.5, "absolute_error": 2e-3}
    assert format_error_text(error).startswith("Erreur")
    set_language("en")
    assert format_error_text(error).startswith("Error")


def test_language_is_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    (tmp_path / ".fluent_prof_generator").mkdir()
    from core.config import ConfigManager

    manager = ConfigManager()
    assert manager.get_language() is None
    manager.save_language("en")
    assert ConfigManager().get_language() == "en"


def test_corrupt_language_entry_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    directory = tmp_path / ".fluent_prof_generator"
    directory.mkdir()
    (directory / "config.json").write_text(
        json.dumps({"language": 42}), encoding="utf-8"
    )
    from core.config import ConfigManager

    assert ConfigManager().get_language() is None
