# TODO: prendre de vraies données si possible via bloomberg

def get_mock_ois_quotes():
    # {maturite_en_annees: taux_swap_ois}
    return {
        1.0: 0.030,
        2.0: 0.032,
        3.0: 0.034,
        5.0: 0.038,
        10.0: 0.040,
    }

def get_mock_ibor_quotes():
    return {
        0.25: 0.039,
        0.5: 0.0385,
        1.0: 0.0375,
        2.0: 0.038,
        5.0: 0.039
    }
