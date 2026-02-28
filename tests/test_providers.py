"""Basic provider registry tests."""

from __future__ import annotations

from tema.providers import DOMAIN_PROVIDERS, PROVIDERS, Provider, get_provider


def test_all_providers_registered() -> None:
    assert len(PROVIDERS) == 7
    expected = {"emailmux", "emailnator", "smailpro", "privatix", "burner", "tempmaili", "etempmail"}
    assert set(PROVIDERS.keys()) == expected


def test_providers_are_provider_instances() -> None:
    for name, p in PROVIDERS.items():
        assert isinstance(p, Provider), f"{name} is not a Provider subclass"


def test_provider_has_required_attrs() -> None:
    for name, p in PROVIDERS.items():
        assert hasattr(p, "name"), f"{name} missing .name"
        assert hasattr(p, "domains"), f"{name} missing .domains"
        assert p.name == name, f"{name}.name == {p.name!r}"
        assert isinstance(p.domains, list), f"{name}.domains is not a list"
        assert len(p.domains) > 0, f"{name}.domains is empty"


def test_domain_providers_coverage() -> None:
    """Every provider referenced in DOMAIN_PROVIDERS must exist."""
    for domain, providers in DOMAIN_PROVIDERS.items():
        for pname in providers:
            assert pname in PROVIDERS, f"DOMAIN_PROVIDERS[{domain!r}] references unknown {pname!r}"


def test_get_provider() -> None:
    p = get_provider("burner")
    assert p.name == "burner"


def test_get_provider_unknown() -> None:
    try:
        get_provider("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
