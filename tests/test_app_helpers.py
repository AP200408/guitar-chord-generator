from pathlib import Path

from generator.ui_state import randomized_parameters
from music.options import (
    ACCIDENTALS,
    CHORD_CHARACTERISTICS,
    COMPLEXITIES,
    KEY_TYPES,
    MINOR_SCALE_TYPES,
    MOODS,
    MUSICAL_CHARACTERS,
    ROOT_NOTES,
)


def test_randomized_parameters_is_valid_and_deterministic():
    randomized = randomized_parameters(12345)
    repeated = randomized_parameters(12345)
    assert randomized == repeated

    assert randomized.root in ROOT_NOTES
    assert randomized.accidental in ACCIDENTALS
    assert randomized.key_type in KEY_TYPES
    assert randomized.complexity in COMPLEXITIES
    assert 1 <= len(randomized.moods) <= 2
    assert 1 <= len(randomized.styles) <= 2
    assert 1 <= len(randomized.characteristics) <= 4
    assert all(mood in MOODS for mood in randomized.moods)
    assert all(style in MUSICAL_CHARACTERS for style in randomized.styles)
    assert all(value in CHORD_CHARACTERISTICS for value in randomized.characteristics)

    if randomized.key_type == "Minor":
        assert randomized.minor_scale_type in MINOR_SCALE_TYPES
    else:
        assert randomized.minor_scale_type == "Natural Minor"


def test_randomization_seed_changes_are_possible():
    outputs = {randomized_parameters(seed) for seed in range(20)}
    assert len(outputs) > 1


def test_randomized_parameters_include_output_controls():
    randomized = randomized_parameters(12345)
    assert 2 <= randomized.chords_per_progression <= 8
    assert 1 <= randomized.progression_count <= 8


def test_copy_button_uses_high_contrast_styles():
    # app.py imports Streamlit and executes page setup at import time; inspect
    # the helper's source contract directly instead of importing the app in
    # the unit-test environment.
    source = Path("app.py").read_text(encoding="utf-8")
    assert "background:#ffffff" in source
    assert "color:#111111" in source
    assert "width:100%; min-width:0" in source
    assert "white-space:nowrap" in source
