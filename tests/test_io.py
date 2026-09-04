"""
Tests de l'extraction des données (shift temporel, Q=0 à t=0).
"""

import numpy as np
import pandas as pd

from core.io import extract_inlet_data, get_max_simulation_time


def test_time_shift_to_zero():
    df = pd.DataFrame({
        "time_ms": [-10.0, 0.0, 30.0, 70.0],
        "Q1": [0.5, 0.6, 0.7, 0.8],
        "T1": [300.0, 301.0, 302.0, 303.0],
    })
    data = extract_inlet_data(df, "time_ms", [("Q1", "T1", 1)])
    np.testing.assert_allclose(data["T_inlet1"]["Time_s"], [0.0, 0.01, 0.04, 0.08])
    np.testing.assert_allclose(data["Q_inlet1"]["Time_s"], [0.0, 0.01, 0.04, 0.08])
    # Q forcé à 0 au premier instant (qui est maintenant t=0)
    assert data["Q_inlet1"]["Value"].iloc[0] == 0.0
    assert get_max_simulation_time(data) == 0.08


def test_no_shift_when_already_zero():
    df = pd.DataFrame({"t": [0.0, 10.0], "Q1": [1.0, 2.0], "T1": [300.0, 301.0]})
    data = extract_inlet_data(df, "t", [("Q1", "T1", 1)])
    np.testing.assert_allclose(data["T_inlet1"]["Time_s"], [0.0, 0.01])


def test_positive_start_is_shifted_not_padded():
    df = pd.DataFrame({"t": [20.0, 30.0], "Q1": [1.0, 2.0], "T1": [300.0, 301.0]})
    data = extract_inlet_data(df, "t", [("Q1", "T1", 1)])
    np.testing.assert_allclose(data["Q_inlet1"]["Time_s"], [0.0, 0.01])
    np.testing.assert_allclose(data["Q_inlet1"]["Value"], [0.0, 2.0])
