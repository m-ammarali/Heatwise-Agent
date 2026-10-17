from agent.risk_scoring import RiskComponents, calculate_heat_risk, primary_driver


def test_low_risk_cool_shaded_site():
    result = calculate_heat_risk(RiskComponents(
        temperature_c=24.0, heat_index_c=24.0, solar_ghi=150.0,
        tree_canopy_pct=35.0, impervious_pct=20.0,
    ))
    assert result.level == "LOW"
    assert 0 <= result.score < 25


def test_critical_risk_hot_exposed_site():
    result = calculate_heat_risk(RiskComponents(
        temperature_c=44.0, heat_index_c=47.0, solar_ghi=950.0,
        tree_canopy_pct=2.0, impervious_pct=90.0,
    ))
    assert result.level == "CRITICAL"
    assert result.score >= 75


def test_score_is_monotonic_in_temperature():
    cool = calculate_heat_risk(RiskComponents(temperature_c=28.0))
    hot = calculate_heat_risk(RiskComponents(temperature_c=41.0))
    assert hot.score > cool.score


def test_vegetation_is_protective():
    bare = calculate_heat_risk(RiskComponents(temperature_c=38.0, tree_canopy_pct=0.0))
    shaded = calculate_heat_risk(RiskComponents(temperature_c=38.0, tree_canopy_pct=30.0))
    assert shaded.score < bare.score


def test_primary_driver_returns_readable_string():
    components = RiskComponents(temperature_c=42.0, solar_ghi=900.0)
    result = calculate_heat_risk(components)
    driver = primary_driver(result, components)
    assert isinstance(driver, str) and len(driver) > 0


def test_list_valued_field_does_not_crash_scoring():
    # Regression test: a live FortyGuard response returned heat_index_celsius
    # as a list instead of a scalar. Scoring must degrade gracefully, not raise.
    result = calculate_heat_risk(RiskComponents(
        temperature_c=38.0,
        heat_index_c=[39.0, 40.5, 41.0],  # type: ignore[arg-type]
    ))
    assert 0 <= result.score <= 100


def test_score_bounds_never_exceeded():
    extreme = calculate_heat_risk(RiskComponents(
        temperature_c=60.0, heat_index_c=60.0, solar_ghi=2000.0,
        tree_canopy_pct=0.0, impervious_pct=100.0,
    ))
    assert 0 <= extreme.score <= 100