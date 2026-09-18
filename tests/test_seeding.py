from pathlib import Path

import pytest

from generator.seeding import (
    MAX_SEED,
    MIN_SEED,
    next_seed,
    random_seed,
    seed_for_action,
    validate_seed,
)


ROOT = Path(__file__).parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def test_seed_validation_accepts_supported_integers():
    assert validate_seed(MIN_SEED) == MIN_SEED
    assert validate_seed(MAX_SEED) == MAX_SEED
    assert validate_seed(123456) == 123456


@pytest.mark.parametrize("value", [-1, MAX_SEED + 1, True, False, 1.5, "123"])
def test_seed_validation_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="Seed"):
        validate_seed(value)


def test_next_seed_advances_and_wraps():
    assert next_seed(MIN_SEED) == MIN_SEED + 1
    assert next_seed(MAX_SEED - 1) == MAX_SEED
    assert next_seed(MAX_SEED) == MIN_SEED


def test_random_seed_is_within_supported_range():
    values = [random_seed() for _ in range(50)]
    assert all(MIN_SEED <= value <= MAX_SEED for value in values)
    assert len(set(values)) > 1


def test_fixed_seed_preserves_generate_and_randomize_seed():
    assert seed_for_action(42, "generate", True) == 42
    assert seed_for_action(42, "randomize", True) == 42


def test_fixed_seed_advances_for_regenerate_and_refine():
    assert seed_for_action(42, "regenerate", True) == 43
    assert seed_for_action(42, "refine", True) == 43


def test_non_fixed_seed_uses_injected_provider():
    assert seed_for_action(42, "generate", False, random_seed_provider=lambda: 777) == 777
    assert seed_for_action(42, "regenerate", False, random_seed_provider=lambda: 888) == 888


def test_non_fixed_seed_rejects_invalid_provider_output():
    with pytest.raises(ValueError, match="Seed"):
        seed_for_action(42, "generate", False, random_seed_provider=lambda: MAX_SEED + 1)


def test_app_exposes_user_facing_seed_controls():
    required_snippets = (
        '"use_fixed_seed": False',
        '"Seed / Reproducibility"',
        '"Use fixed seed"',
        'st.number_input(',
        '"Seed"',
        '"🎲 New seed"',
        '"A fresh random seed is used for each generation action."',
        'seed_for_action',
        'Seed: {seed_used} ({seed_mode})',
        '"seed": used_seed',
        '"seed_mode": "fixed" if st.session_state.use_fixed_seed else "automatic"',
    )
    for snippet in required_snippets:
        assert snippet in APP_SOURCE


def test_pending_seed_is_prepared_before_seed_widget_instantiation():
    assert 'def _prepare_pending_seed()' in APP_SOURCE
    assert '_prepare_pending_seed()' in APP_SOURCE
    assert APP_SOURCE.index('_prepare_pending_seed()') < APP_SOURCE.index('with st.sidebar:')
    assert 'used_seed = st.session_state.generation_seed' in APP_SOURCE
    assert 'seed=used_seed' in APP_SOURCE


def test_fixed_seed_seed_is_advanced_for_regeneration_in_app_flow():
    assert 'seed_for_action(' in APP_SOURCE
    assert "        action,\n        st.session_state.use_fixed_seed," in APP_SOURCE
    assert 'if action is None or action.startswith("refine:")' in APP_SOURCE


def test_generation_does_not_mutate_widget_seed_after_sidebar_instantiation():
    sidebar_index = APP_SOURCE.index('with st.sidebar:')
    generation_index = APP_SOURCE.index('pending_action = st.session_state.pending_action')
    post_sidebar = APP_SOURCE[sidebar_index:generation_index]
    assert 'st.session_state.generation_seed =' not in post_sidebar

