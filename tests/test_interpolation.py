"""
Tests des méthodes d'interpolation, des zones et de leurs combinaisons.
"""

import itertools

import numpy as np
import pandas as pd
import pytest

from core.constants import INTERP_METHODS
from core.interpolation import (
    interpolate, interpolate_all_data, generate_time_array,
    zones_to_index_ranges, normalize_zones, sanitize_flow, _difference_matrix,
)

METHODS = list(INTERP_METHODS.keys())


def make_df(n=60, noise=0.02, seed=0, t_end=0.5):
    rng = np.random.RandomState(seed)
    x = np.linspace(0, t_end, n)
    y = 300 + 20 * np.sin(2 * np.pi * x / t_end) + noise * rng.randn(n)
    return pd.DataFrame({"Time_s": x, "Value": y})


def make_nonuniform_df(seed=0):
    """Grille irrégulière avec deux points quasi dupliqués (0.1 ms d'écart)."""
    rng = np.random.RandomState(seed)
    x = np.sort(np.concatenate([np.linspace(0, 0.5, 40), [0.0849, 0.0850, 0.31]]))
    x = np.unique(x)
    y = 300 + 20 * np.sin(2 * np.pi * x / 0.5) + 0.5 * rng.randn(len(x))
    return pd.DataFrame({"Time_s": x, "Value": y})


ZONE_SETS = {
    "none": [],
    "exact_mid": [(0.2, 0.3, "exact")],
    "linear_mid": [(0.2, 0.3, "linear")],
    "two": [(0.05, 0.1, "exact"), (0.3, 0.4, "linear")],
    "tiny": [(0.2001, 0.2002, "exact")],
    "at_start": [(0.0, 0.05, "linear")],
    "at_end": [(0.45, 0.5, "exact")],
    "touching": [(0.1, 0.2, "exact"), (0.2, 0.3, "linear")],
    "legacy_2tuple": [(0.2, 0.3)],
    "reversed_bounds": [(0.3, 0.2, "linear")],
    "overlapping": [(0.1, 0.25, "exact"), (0.2, 0.35, "linear")],
    "beyond_end": [(0.6, 0.7, "exact")],
}


@pytest.mark.parametrize("method,zone_name", list(itertools.product(METHODS, ZONE_SETS.keys())))
def test_all_combinations_are_finite_and_continuous(method, zone_name):
    df = make_df()
    zones = ZONE_SETS[zone_name]
    t = np.linspace(0, 0.5, 5001)
    y = interpolate(df, t, method=method, smooth_factor=0.01,
                    unfiltered_zones=zones, trend_lambda=5.0)

    assert y.shape == t.shape
    assert np.all(np.isfinite(y))

    # Continuité : aucun saut plus grand que 3x le plus grand pas de la
    # référence linéaire brute (sur une grille 5000 pts, un vrai saut est
    # des dizaines de fois plus grand).
    ref_step = np.abs(np.diff(np.interp(t, df["Time_s"], df["Value"]))).max()
    assert np.abs(np.diff(y)).max() <= 3 * ref_step + 1e-9


@pytest.mark.parametrize("method", METHODS)
def test_exact_zone_passes_through_raw_points(method):
    df = make_df()
    zones = [(0.2, 0.3, "exact")]
    i0, i1, _ = zones_to_index_ranges(df["Time_s"].to_numpy(), zones)[0]
    x_zone = df["Time_s"].to_numpy()[i0:i1 + 1]
    y_zone = df["Value"].to_numpy()[i0:i1 + 1]
    y = interpolate(df, x_zone, method=method, unfiltered_zones=zones, trend_lambda=5.0)
    np.testing.assert_allclose(y, y_zone, atol=1e-9)


@pytest.mark.parametrize("method", METHODS)
def test_linear_zone_is_straight_line(method):
    df = make_df()
    zones = [(0.2, 0.3, "linear")]
    x = df["Time_s"].to_numpy()
    yv = df["Value"].to_numpy()
    i0, i1, _ = zones_to_index_ranges(x, zones)[0]
    t = np.linspace(x[i0], x[i1], 50)
    expected = yv[i0] + (yv[i1] - yv[i0]) * (t - x[i0]) / (x[i1] - x[i0])
    y = interpolate(df, t, method=method, unfiltered_zones=zones, trend_lambda=5.0)
    np.testing.assert_allclose(y, expected, atol=1e-9)


@pytest.mark.parametrize("method", METHODS)
def test_boundary_values_are_raw_at_zone_edges(method):
    """Continuité C0 : la valeur aux frontières d'une zone est la valeur mesurée."""
    df = make_df()
    zones = [(0.2, 0.3, "exact")]
    x = df["Time_s"].to_numpy()
    yv = df["Value"].to_numpy()
    i0, i1, _ = zones_to_index_ranges(x, zones)[0]
    eps = 1e-7
    for i in (i0, i1):
        left = interpolate(df, np.array([x[i] - eps]), method=method,
                           unfiltered_zones=zones, trend_lambda=5.0)[0]
        right = interpolate(df, np.array([x[i] + eps]), method=method,
                            unfiltered_zones=zones, trend_lambda=5.0)[0]
        assert abs(left - yv[i]) < 1e-3
        assert abs(right - yv[i]) < 1e-3


@pytest.mark.parametrize("method", METHODS)
def test_no_extrapolation_beyond_data(method):
    df = make_df(t_end=0.4)
    t = np.linspace(0, 0.6, 601)
    y = interpolate(df, t, method=method, trend_lambda=5.0)
    last_raw = df["Value"].iloc[-1]
    # Prolongement constant : toutes les valeurs après 0.4 s sont égales
    after = y[t > 0.4]
    np.testing.assert_allclose(after, after[0])
    assert abs(after[0] - last_raw) < 2.0  # proche de la dernière mesure
    before = y[t < 0]
    assert before.size == 0


@pytest.mark.parametrize("method", ["trend_l2", "trend_l1", "spline"])
def test_nonuniform_grid_no_spike_at_close_points(method):
    df = make_nonuniform_df()
    t = np.linspace(0, 0.5, 5001)
    y = interpolate(df, t, method=method, smooth_factor=0.01, trend_lambda=5.0)
    ref_step = np.abs(np.diff(np.interp(t, df["Time_s"], df["Value"]))).max()
    assert np.abs(np.diff(y)).max() <= 3 * ref_step


def test_difference_matrix_reduces_to_classic_on_uniform_grid():
    x = np.linspace(0, 1, 7)
    D2 = _difference_matrix(x, 2).toarray()
    np.testing.assert_allclose(D2[0, :3], [1, -2, 1])
    np.testing.assert_allclose(D2[2, 2:5], [1, -2, 1])
    D1 = _difference_matrix(x, 1).toarray()
    np.testing.assert_allclose(D1[0, :2], [-1, 1])


def test_trend_l2_smooths_noise():
    df = make_df(noise=2.0)
    x = df["Time_s"].to_numpy()
    y = interpolate(df, x, method="trend_l2", trend_lambda=20.0)
    clean = 300 + 20 * np.sin(2 * np.pi * x / 0.5)
    assert np.std(y - clean) < np.std(df["Value"].to_numpy() - clean)


def test_zones_to_index_ranges_rules():
    x = np.linspace(0, 1, 11)  # pas 0.1
    # zone plus fine que le pas -> élargie à 2 points
    assert zones_to_index_ranges(x, [(0.201, 0.202, "exact")]) == [(2, 3, "exact")]
    # chevauchement -> la 2e zone commence à la fin de la 1re
    r = zones_to_index_ranges(x, [(0.1, 0.5, "exact"), (0.4, 0.8, "linear")])
    assert r == [(1, 5, "exact"), (5, 8, "linear")]
    # zone au-delà des données -> ignorée
    assert zones_to_index_ranges(x, [(1.5, 2.0, "exact")]) == []
    # bornes inversées -> réordonnées ; tuple à 2 éléments -> exact
    assert normalize_zones([(0.5, 0.2), [0.7, 0.9, "linear"]]) == [
        (0.2, 0.5, "exact"), (0.7, 0.9, "linear")
    ]
    # type inconnu -> exact
    assert normalize_zones([(0.1, 0.2, "foo")]) == [(0.1, 0.2, "exact")]


def test_generate_time_array_exact_step():
    t = generate_time_array(0.495, 1e-6)
    assert len(t) == 495001
    np.testing.assert_allclose(np.diff(t), 1e-6, rtol=0, atol=1e-15)
    assert t[0] == 0.0
    assert t[-1] <= 0.495 + 1e-12
    with pytest.raises(ValueError):
        generate_time_array(0.0, 1e-6)
    with pytest.raises(ValueError):
        generate_time_array(1.0, 0.0)


def test_sanitize_flow():
    v, n = sanitize_flow(np.array([0.0, 1.0, 0.0]), 1e-5)
    assert n == 2
    np.testing.assert_allclose(v, [1e-5, 1.0, 1e-5])


def test_interpolate_all_data_inversion_and_rename():
    df_q = make_df(seed=1)
    df_q.loc[0, "Value"] = 0.0
    df_t = make_df(seed=2)
    data = {"Q_inlet1": df_q, "T_inlet1": df_t}
    times = generate_time_array(0.5, 1e-3)
    out = interpolate_all_data(
        data, times, {"Q_inlet1": "linear", "T_inlet1": "pchip"}, {},
        flow_eps=1e-5, unfiltered_zones={}, inlet_names={"inlet1": "tul"},
        trend_lambda_params={}, inverted={"Q_inlet1": True},
    )
    assert set(out) == {"Q_tul", "T_tul"}
    # Inversion appliquée partout, y compris au remplacement du débit nul
    assert out["Q_tul"][0] == -1e-5
    np.testing.assert_allclose(out["Q_tul"][1:], -np.interp(times[1:], df_q["Time_s"], df_q["Value"]))
    np.testing.assert_allclose(out["T_tul"], interpolate(df_t, times, method="pchip"))


def test_too_few_points_raises():
    df = pd.DataFrame({"Time_s": [0, 1, 2], "Value": [1, 2, 3]})
    with pytest.raises(ValueError):
        interpolate(df, np.array([0.5]), method="pchip")
    # Linéaire accepte 2 points
    df2 = pd.DataFrame({"Time_s": [0, 1], "Value": [1, 3]})
    np.testing.assert_allclose(interpolate(df2, np.array([0.5]), method="linear"), [2.0])


def test_duplicate_and_unsorted_times_are_cleaned():
    df = pd.DataFrame({"Time_s": [0.3, 0.0, 0.1, 0.1, 0.2, 0.4, 0.5],
                       "Value": [3.0, 0.0, 1.0, 9.0, 2.0, 4.0, 5.0]})
    y = interpolate(df, np.array([0.05, 0.15]), method="linear")
    np.testing.assert_allclose(y, [0.5, 1.5])


@pytest.mark.parametrize("method", ["trend_l1", "trend_l2"])
def test_trend_filter_smoothing_is_scale_invariant(method):
    """
    Une même forme de courbe doit être lissée dans les mêmes proportions
    quelle que soit son amplitude. Le L1 ne l'était pas : à lambda égal, une
    température de plusieurs centaines de kelvins restait quasi intacte
    alors qu'un débit de quelques unités était fortement lissé.
    """
    rng = np.random.RandomState(3)
    x = np.linspace(0, 0.5, 80)
    shape = np.sin(2 * np.pi * x / 0.5) + 0.15 * rng.randn(80)
    t = np.linspace(0, 0.5, 2000)

    ratios = []
    for amplitude in (1.0, 300.0):
        y = 350.0 + amplitude * shape
        df = pd.DataFrame({"Time_s": x, "Value": y})
        z = interpolate(df, x, method=method, trend_lambda=5.0)
        ratios.append(np.sqrt(np.mean((z - y) ** 2)) / amplitude)

    assert ratios[0] > 0.01, "le lissage doit avoir un effet mesurable"
    assert ratios[1] == pytest.approx(ratios[0], rel=0.05)


def test_trend_l1_leaves_linear_data_untouched():
    df = pd.DataFrame({"Time_s": np.linspace(0, 1, 30), "Value": 2.0 * np.linspace(0, 1, 30) + 1.0})
    z = interpolate(df, df["Time_s"].to_numpy(), method="trend_l1", trend_lambda=50.0)
    np.testing.assert_allclose(z, df["Value"].to_numpy(), atol=1e-9)
