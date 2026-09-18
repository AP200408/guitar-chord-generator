from dataclasses import replace
from pathlib import Path

import pytest

from generator.progression import generate_progressions
from generator.result_tools import (
    refinement_help,
    refinement_is_available,
    refinement_label,
    refine_parameters,
)
from music.models import GeneratorParameters
from music.options import MOODS

ROOT = Path(__file__).parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def make_params(**overrides) -> GeneratorParameters:
    base = GeneratorParameters(
        key=GeneratorParameters.build_key("C", "Normal", "Major"),
        moods=("Dreamy",),
        styles=("Neo Soul",),
        complexity="Intermediate",
        characteristics=("Maj7", "9th"),
        chords_per_progression=4,
        progression_count=3,
        start_degree=2,
        end_degree=1,
        tension_preference="High",
        resolution_preference="Strong Cadence",
        voice_leading_preference="Smooth",
        required_degrees=(),
        excluded_degrees=(),
        max_difficulty="Any",
        chord_families=(),
    )
    return replace(base, **overrides)


def test_refinement_labels_and_help_are_stable():
    assert refinement_label("simpler") == "Make simpler"
    assert refinement_label("complex") == "Make more complex"
    assert refinement_label("new_progression") == "New progression"
    assert refinement_label("new_mood") == "New mood"
    for action in ("simpler", "complex", "new_progression", "new_mood"):
        assert refinement_help(action)


@pytest.mark.parametrize(
    ("complexity", "action", "expected"),
    [
        ("Beginner", "simpler", "Beginner"),
        ("Intermediate", "simpler", "Beginner"),
        ("Advanced", "simpler", "Intermediate"),
        ("Experimental", "simpler", "Advanced"),
        ("Beginner", "complex", "Intermediate"),
        ("Intermediate", "complex", "Advanced"),
        ("Advanced", "complex", "Experimental"),
        ("Experimental", "complex", "Experimental"),
    ],
)
def test_complexity_refinements_move_one_step_and_preserve_other_parameters(
    complexity, action, expected
):
    original = make_params(complexity=complexity)
    refined = refine_parameters(original, action)
    assert refined.complexity == expected
    assert replace(refined, complexity=original.complexity) == original


def test_new_progression_keeps_every_generation_parameter():
    original = make_params(
        moods=("Dreamy", "Soulful"),
        styles=("Neo Soul", "R&B"),
        characteristics=("Maj7", "9th", "6/9"),
        required_degrees=(1, 5),
        max_difficulty="Advanced",
        chord_families=("Sevenths", "Extensions"),
    )
    assert refine_parameters(original, "new_progression") == original


def test_new_mood_changes_only_moods_and_preserves_all_other_settings():
    original = make_params(moods=("Dreamy", "Soulful"))
    refined = refine_parameters(original, "new_mood", seed=12345)
    assert refined.moods
    assert refined.moods != original.moods
    assert all(mood in MOODS for mood in refined.moods)
    assert set(refined.moods).isdisjoint(set(original.moods))
    assert replace(refined, moods=original.moods) == original


def test_new_mood_is_deterministic_for_a_seed():
    original = make_params(moods=("Dreamy",))
    first = refine_parameters(original, "new_mood", seed=77)
    second = refine_parameters(original, "new_mood", seed=77)
    assert first == second


def test_new_mood_handles_all_moods_without_returning_the_full_selection():
    original = make_params(moods=tuple(MOODS))
    refined = refine_parameters(original, "new_mood", seed=1)
    assert len(refined.moods) == 1
    assert refined.moods[0] in MOODS


@pytest.mark.parametrize("complexity", ["Intermediate", "Advanced", "Experimental"])
def test_refined_generation_remains_valid_for_complexity_actions(complexity):
    original = make_params(complexity=complexity, progression_count=2)
    action = "simpler" if complexity != "Beginner" else "complex"
    refined = refine_parameters(original, action)
    result = generate_progressions(refined, seed=8080)
    assert len(result.all_progressions) == refined.progression_count
    assert all(len(item.chords) == refined.chords_per_progression for item in result.all_progressions)


def test_new_mood_refinement_generates_valid_results_without_changing_key_or_style():
    original = make_params(progression_count=2)
    refined = refine_parameters(original, "new_mood", seed=8081)
    result = generate_progressions(refined, seed=8081)
    assert refined.key == original.key
    assert refined.styles == original.styles
    assert len(result.all_progressions) == 2


def test_refinement_availability_matches_complexity_boundaries():
    assert not refinement_is_available(make_params(complexity="Beginner"), "simpler")
    assert refinement_is_available(make_params(complexity="Intermediate"), "simpler")
    assert refinement_is_available(make_params(complexity="Advanced"), "simpler")
    assert refinement_is_available(make_params(complexity="Beginner"), "complex")
    assert refinement_is_available(make_params(complexity="Advanced"), "complex")
    assert not refinement_is_available(make_params(complexity="Experimental"), "complex")
    assert refinement_is_available(make_params(complexity="Experimental"), "new_progression")
    assert refinement_is_available(make_params(complexity="Experimental"), "new_mood")


def test_invalid_refinement_action_is_rejected():
    with pytest.raises(ValueError, match="Unsupported refinement action"):
        refine_parameters(make_params(), "invalid")


def test_app_integrates_step5_refinement_controls():
    assert 'Refine this result' in APP_SOURCE
    assert 'refinement_label(action)' in APP_SOURCE
    assert 'refinement_help(action)' in APP_SOURCE
    assert 'refinement_actions = ("simpler", "complex", "new_progression", "new_mood")' in APP_SOURCE

    assert "def _apply_refinement" in APP_SOURCE
    assert "refinement_is_available" in APP_SOURCE
    assert "_sync_session_to_parameters" in APP_SOURCE
    assert 'st.session_state.pending_action = f"refine:{action}"' in APP_SOURCE


def test_refinement_controls_disable_boundary_actions():
    assert 'disabled=not refinement_is_available(active_parameters, action)' in APP_SOURCE
    assert 'key=f"refine-{action}"' in APP_SOURCE


def test_regenerate_refinement_uses_refined_parameters_and_is_seed_reproducible():
    from generator.result_tools import regenerate_refinement

    original = make_params(progression_count=2)
    first = regenerate_refinement(original, "new_progression", seed=9001)
    second = regenerate_refinement(original, "new_progression", seed=9001)
    assert [item.display_name for item in first.all_progressions] == [
        item.display_name for item in second.all_progressions
    ]
    assert [item.score for item in first.all_progressions] == [
        item.score for item in second.all_progressions
    ]
