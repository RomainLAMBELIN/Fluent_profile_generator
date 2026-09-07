"""
Tests de l'analyse des pentes : mesure de la reduction des variations brusques.
"""

import numpy as np
import pytest

from core.analysis import (
    slopes_between_samples, slopes_along_curve, max_slope,
    slope_reduction_percent, format_slope_value,
)


def test_slopes_between_samples_on_known_segments():
    x = np.array([0.0, 1.0, 2.0, 4.0])
    y = np.array([0.0, 3.0, 3.0, -1.0])
    mids, slopes = slopes_between_samples(x, y)
    np.testing.assert_allclose(slopes, [3.0, 0.0, -2.0])
    np.testing.assert_allclose(mids, [0.5, 1.5, 3.0])


def test_slopes_between_samples_needs_two_points():
    mids, slopes = slopes_between_samples([1.0], [2.0])
    assert mids.size == 0 and slopes.size == 0


def test_slopes_along_curve_matches_analytic_derivative():
    t = np.linspace(0, 1, 2001)
    y = np.sin(2 * np.pi * t)
    _, slopes = slopes_along_curve(t, y)
    expected = 2 * np.pi * np.cos(2 * np.pi * t)
    assert np.max(np.abs(slopes - expected)) < 1e-3


def test_max_slope_finds_steepest_signed_value_and_position():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([0.0, 1.0, -9.0, -9.0])
    mids, slopes = slopes_between_samples(x, y)
    result = max_slope(mids, slopes)
    assert result["value"] == pytest.approx(-10.0)
    assert result["magnitude"] == pytest.approx(10.0)
    assert result["time"] == pytest.approx(1.5)


def test_max_slope_on_empty_or_non_finite():
    assert max_slope(np.array([]), np.array([])) is None
    assert max_slope(np.array([0.0, 1.0]), np.array([np.nan, np.nan])) is None


def test_max_slope_ignores_non_finite_values():
    result = max_slope(np.array([0.0, 1.0, 2.0]), np.array([np.nan, 4.0, 2.0]))
    assert result["magnitude"] == pytest.approx(4.0)
    assert result["time"] == pytest.approx(1.0)


def test_slope_reduction_percent():
    raw = {"magnitude": 100.0, "value": 100.0, "time": 0.0}
    smoothed = {"magnitude": 25.0, "value": 25.0, "time": 0.0}
    assert slope_reduction_percent(raw, smoothed) == pytest.approx(75.0)
    # Un traitement qui durcit la courbe donne une valeur negative
    harder = {"magnitude": 150.0, "value": 150.0, "time": 0.0}
    assert slope_reduction_percent(raw, harder) == pytest.approx(-50.0)


def test_slope_reduction_percent_edge_cases():
    zero = {"magnitude": 0.0, "value": 0.0, "time": 0.0}
    other = {"magnitude": 5.0, "value": 5.0, "time": 0.0}
    assert slope_reduction_percent(zero, other) is None
    assert slope_reduction_percent(None, other) is None
    assert slope_reduction_percent(other, None) is None


@pytest.mark.parametrize("value,expected", [
    (0.0, "0"), (1234.5678, "1235"), (-0.5, "-0.5"),
    (1.5e7, "1.500e+07"), (3e-6, "3.000e-06"),
])
def test_format_slope_value(value, expected):
    assert format_slope_value(value) == expected


def test_smoothing_reduces_max_slope_end_to_end():
    """Le cas d'usage : verifier qu'un lissage adoucit reellement la courbe."""
    import pandas as pd
    from core.interpolation import interpolate

    rng = np.random.RandomState(0)
    x = np.linspace(0, 0.5, 80)
    y = 300 + 20 * np.sin(2 * np.pi * x / 0.5) + 3.0 * rng.randn(80)
    df = pd.DataFrame({"Time_s": x, "Value": y})

    raw = max_slope(*slopes_between_samples(x, y))
    t = np.linspace(0, 0.5, 4000)
    smoothed_curve = interpolate(df, t, method="trend_l2", trend_lambda=50.0)
    smoothed = max_slope(*slopes_along_curve(t, smoothed_curve))

    reduction = slope_reduction_percent(raw, smoothed)
    assert reduction > 50.0
    assert 0.0 <= smoothed["time"] <= 0.5
