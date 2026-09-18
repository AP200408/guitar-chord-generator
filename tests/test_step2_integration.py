from pathlib import Path

import pytest

from generator.progression import generate_progressions
from generator.ui_state import randomized_parameters
from music.models import GeneratorParameters

ROOT = Path(__file__).parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def make_params(**overrides) -> GeneratorParameters:
    values = dict(
        key=GeneratorParameters.build_key("C", "Normal", "Major"),
        moods=("Dreamy",),
        styles=("Neo Soul",),
        complexity="Intermediate",
        characteristics=("Maj7", "9th"),
        chords_per_progression=4,
        progression_count=4,
        start_degree=None,
        end_degree=None,
        tension_preference="Balanced",
        resolution_preference="Flexible",
        voice_leading_preference="Balanced",
    )
    values.update(overrides)
    return GeneratorParameters(**values)


def test_step2_default_behavior_remains_four_progressions_of_four_chords():
    result = generate_progressions(make_params(), seed=2026)
    assert len(result.all_progressions) == 4
    assert all(len(item.chords) == 4 for item in result.all_progressions)


@pytest.mark.parametrize("length", range(2, 9))
def test_all_supported_progression_lengths_remain_valid(length):
    result = generate_progressions(make_params(chords_per_progression=length), seed=100 + length)
    assert all(len(item.chords) == length for item in result.all_progressions)


@pytest.mark.parametrize("start", range(1, 8))
@pytest.mark.parametrize("end", range(1, 8))
def test_start_and_end_degree_controls_are_hard_constraints(start, end):
    result = generate_progressions(
        make_params(
            chords_per_progression=4,
            progression_count=2,
            start_degree=start,
            end_degree=end,
        ),
        seed=(start * 10) + end,
    )
    for progression in result.all_progressions:
        assert progression.degrees[0] == start
        assert progression.degrees[-1] == end
        assert progression.chords[0].roman_numeral
        assert progression.chords[-1].roman_numeral
        assert len(progression.functions) == 4
        assert len(progression.tensions) == 4


@pytest.mark.parametrize("minor_scale_type", ["Natural Minor", "Harmonic Minor", "Melodic Minor"])
def test_step2_controls_work_for_all_minor_scale_types(minor_scale_type):
    params = make_params(
        key=GeneratorParameters.build_key("A", "Normal", "Minor", minor_scale_type),
        chords_per_progression=5,
        start_degree=2,
        end_degree=1,
        tension_preference="High",
        resolution_preference="Strong Cadence",
        voice_leading_preference="Smooth",
    )
    result = generate_progressions(params, seed=77)
    assert all(item.degrees[0] == 2 and item.degrees[-1] == 1 for item in result.all_progressions)
    assert all(all(0.0 <= value <= 1.0 for value in item.tensions) for item in result.all_progressions)


@pytest.mark.parametrize("resolution", ["Flexible", "Prefer Tonic", "Strong Cadence"])
@pytest.mark.parametrize("voice", ["Balanced", "Smooth", "Expressive"])
def test_resolution_and_voice_preferences_generate_valid_results(resolution, voice):
    result = generate_progressions(
        make_params(
            resolution_preference=resolution,
            voice_leading_preference=voice,
            progression_count=3,
        ),
        seed=4242,
    )
    assert len(result.all_progressions) == 3
    assert all(item.score == float(item.score) for item in result.all_progressions)


def test_harmonic_function_metadata_matches_degrees():
    result = generate_progressions(make_params(), seed=31415)
    for progression in result.all_progressions:
        assert len(progression.functions) == len(progression.chords)
        assert all(progression.functions)
        assert progression.functions[0] in {"Tonic", "Predominant", "Dominant", "Color", "Passing"}


def test_same_seed_is_reproducible_with_step2_controls():
    params = make_params(
        start_degree=2,
        end_degree=1,
        tension_preference="High",
        resolution_preference="Strong Cadence",
        voice_leading_preference="Smooth",
    )
    first = generate_progressions(params, seed=9876)
    second = generate_progressions(params, seed=9876)
    assert [item.display_name for item in first.all_progressions] == [
        item.display_name for item in second.all_progressions
    ]
    assert [item.score for item in first.all_progressions] == [
        item.score for item in second.all_progressions
    ]


def test_randomized_parameters_include_all_step2_controls_and_are_deterministic():
    first = randomized_parameters(5150)
    second = randomized_parameters(5150)
    assert first == second
    assert first.start_degree is None or 1 <= first.start_degree <= 7
    assert first.end_degree is None or 1 <= first.end_degree <= 7
    assert first.tension_preference in {"Low", "Balanced", "High"}
    assert first.resolution_preference in {"Flexible", "Prefer Tonic", "Strong Cadence"}
    assert first.voice_leading_preference in {"Balanced", "Smooth", "Expressive"}


def test_app_exposes_step4_filter_controls():
    for label in (
        '"Filters"',
        '"Require scale degrees"',
        '"Exclude scale degrees"',
        '"Maximum result difficulty"',
        '"Allowed chord families"',
    ):
        assert label in APP_SOURCE

    for state_key in (
        '"required_degrees"',
        '"excluded_degrees"',
        '"max_difficulty"',
        '"chord_families"',
    ):
        assert state_key in APP_SOURCE


def test_app_exposes_step2_harmony_controls():
    for label in (
        '"Starting Chord"',
        '"Ending Chord"',
        '"Tension"',
        '"Resolution"',
        '"Voice Leading"',
        '"Harmony Controls"',
    ):
        assert label in APP_SOURCE

    for state_key in (
        '"start_degree"',
        '"end_degree"',
        '"tension_preference"',
        '"resolution_preference"',
        '"voice_leading_preference"',
    ):
        assert state_key in APP_SOURCE

    assert "harmonic function:" in APP_SOURCE.lower()
    assert "degree_choices()" in APP_SOURCE
