"""
Tests de la configuration utilisateur.

Une configuration ecrite par une version anterieure, incomplete ou
corrompue ne doit jamais empecher l'application de demarrer.
"""

import json

import pytest

from core.config import ConfigManager


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    """Isole la configuration dans un dossier temporaire."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    directory = tmp_path / ".fluent_prof_generator"
    directory.mkdir()
    return directory


def write_config(config_dir, data):
    (config_dir / "config.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


VALID_MAPPING = {
    "time_col": "time_ms",
    "inlets": [
        {"q_col": "Q1", "t_col": "T1", "name": "tulipe"},
        {"q_col": "Q2", "t_col": "T2", "name": "tige"},
    ],
}


def test_valid_mapping_is_restored(config_dir):
    write_config(config_dir, {"last_column_mapping": VALID_MAPPING})
    mapping = ConfigManager().get_last_column_mapping()
    assert mapping["time_col"] == "time_ms"
    assert [i["q_col"] for i in mapping["inlets"]] == ["Q1", "Q2"]
    assert [i["name"] for i in mapping["inlets"]] == ["tulipe", "tige"]


@pytest.mark.parametrize("inlets", [
    [{"Q": "Q1", "T": "T1", "name": "tulipe"}],            # ancien format
    [{"q_col": "Q1", "name": "tulipe"}],                   # t_col absent
    [{"q_col": "", "t_col": "T1"}],                        # colonne vide
    [{"q_col": 1, "t_col": 2}],                            # types errones
    ["Q1"],                                                # pas un dict
    [],                                                    # liste vide
])
def test_unusable_mapping_is_ignored_not_fatal(config_dir, inlets):
    """Le cas rencontre en production : KeyError au demarrage."""
    write_config(config_dir, {
        "last_column_mapping": {"time_col": "time_ms", "inlets": inlets}
    })
    mapping = ConfigManager().get_last_column_mapping()
    assert mapping == {}


def test_partially_valid_mapping_is_rejected_as_a_whole(config_dir):
    """Restaurer une partie des inlets donnerait un mapping trompeur."""
    write_config(config_dir, {"last_column_mapping": {
        "time_col": "time_ms",
        "inlets": [
            {"Q": "Q1", "T": "T1"},
            {"q_col": "Q2", "t_col": "T2", "name": "tige"},
        ],
    }})
    assert ConfigManager().get_last_column_mapping() == {}


def test_mapping_without_name_gets_a_default(config_dir):
    write_config(config_dir, {"last_column_mapping": {
        "time_col": "t",
        "inlets": [{"q_col": "Q1", "t_col": "T1"}],
    }})
    mapping = ConfigManager().get_last_column_mapping()
    assert mapping["inlets"][0]["name"] == "inlet1"


def test_inlet_names_keys_become_integers(config_dir):
    """JSON n'a que des cles textuelles ; le code cherche par entier."""
    write_config(config_dir, {"last_inlet_names": {"1": "tulipe", "2": "tige"}})
    names = ConfigManager().get_last_inlet_names()
    assert names == {1: "tulipe", 2: "tige"}
    assert names.get(1) == "tulipe"


def test_inlet_names_drops_unusable_entries(config_dir):
    write_config(config_dir, {"last_inlet_names": {
        "1": "tulipe", "abc": "x", "2": "", "3": 42,
    }})
    assert ConfigManager().get_last_inlet_names() == {1: "tulipe"}


def test_step2_params_filtered_by_type(config_dir):
    write_config(config_dir, {"last_step2_params": {
        "dt_us": 2.5,
        "flow_eps": "pas un nombre",
        "methods": {"Q_inlet1": "pchip"},
        "smooth_params": "pas un dict",
    }})
    params = ConfigManager().get_last_step2_params()
    assert params["dt_us"] == 2.5
    assert "flow_eps" not in params
    assert params["methods"] == {"Q_inlet1": "pchip"}
    assert "smooth_params" not in params


@pytest.mark.parametrize("raw", ['["une", "liste"]', "pas du json", "null"])
def test_corrupt_config_file_is_survivable(config_dir, raw):
    (config_dir / "config.json").write_text(raw, encoding="utf-8")
    manager = ConfigManager()
    assert manager.get_last_column_mapping() == {}
    assert manager.get_last_inlet_names() == {}
    assert manager.get_last_step2_params() == {}


def test_roundtrip_save_then_read(config_dir):
    manager = ConfigManager()
    manager.save_last_column_mapping(VALID_MAPPING)
    manager.save_last_inlet_names({1: "tulipe", 2: "tige"})
    reread = ConfigManager()
    assert reread.get_last_column_mapping()["inlets"][1]["q_col"] == "Q2"
    assert reread.get_last_inlet_names() == {1: "tulipe", 2: "tige"}
