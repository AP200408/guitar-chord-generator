import pytest

from generator.harmony_rules import (
    FUNCTION_NAMES,
    chord_function,
    chord_tension,
    degree_choices,
    degree_function,
    functional_sequence_score,
    resolution_score,
    target_tension_score,
    transition_function_score,
    validate_progression_preferences,
    voice_leading_quality,
    voice_leading_score,
)
from music.chord_qualities import build_chord
from music.key_chords import get_chords_in_key
from music.models import Key
from music.options import (
    RESOLUTION_PREFERENCES,
    TENSION_LEVELS,
    VOICE_LEADING_PREFERENCES,
)


def test_degree_choices_include_any_and_all_scale_degrees():
    assert degree_choices() == (None, 1, 2, 3, 4, 5, 6, 7)


@pytest.mark.parametrize("mode", ["Major", "Minor"])
def test_all_scale_degrees_have_a_broad_function(mode):
    key = Key("C", "Normal", mode)
    assert all(degree_function(key, degree) in FUNCTION_NAMES for degree in range(1, 8))


def test_major_function_map_is_explicit():
    key = Key("C", "Normal", "Major")
    assert [degree_function(key, degree) for degree in range(1, 8)] == [
        "Tonic", "Predominant", "Color", "Predominant", "Dominant", "Tonic", "Dominant"
    ]


def test_minor_function_map_is_explicit():
    key = Key("A", "Normal", "Minor")
    assert [degree_function(key, degree) for degree in range(1, 8)] == [
        "Tonic", "Predominant", "Color", "Predominant", "Dominant", "Tonic", "Dominant"
    ]


def test_chord_function_uses_roman_numeral_when_degree_is_omitted():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    assert chord_function(chords[0], key) == "Tonic"
    assert chord_function(chords[4], key) == "Dominant"


def test_invalid_degree_function_is_rejected():
    with pytest.raises(ValueError, match="Scale degree must be between 1 and 7"):
        degree_function(Key("C", "Normal", "Major"), 8)


def test_structural_tension_is_bounded_and_function_aware():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    tonic = chord_tension(chords[0], key, 1)
    dominant = chord_tension(chords[4], key, 5)
    assert 0.0 <= tonic <= 1.0
    assert 0.0 <= dominant <= 1.0
    assert dominant > tonic


def test_functional_resolution_scores_v_to_i():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    score = transition_function_score(chords[4], chords[0], key)
    assert score > 0
    assert transition_function_score(chords[0], chords[0], key) < score


def test_functional_sequence_score_rewards_predominant_dominant_tonic_motion():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    ii_v_i = (chords[1], chords[4], chords[0])
    i_iii_vi = (chords[0], chords[2], chords[5])
    assert functional_sequence_score(ii_v_i, key) > functional_sequence_score(i_iii_vi, key)


def test_target_tension_score_prefers_matching_target():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    low = (chords[0], chords[3], chords[0])
    high = (chords[4], chords[6], chords[4])
    assert target_tension_score(low, key, "Low") > target_tension_score(low, key, "High")
    assert target_tension_score(high, key, "High") > target_tension_score(high, key, "Low")


def test_resolution_preferences_distinguish_flexible_prefer_tonic_and_strong_cadence():
    key = Key("C", "Normal", "Major")
    chords = get_chords_in_key(key)
    v_i = (chords[4], chords[0])
    ii_i = (chords[1], chords[0])

    assert resolution_score(v_i, key, "Flexible") == 0.0
    assert resolution_score(v_i, key, "Prefer Tonic") > 0
    assert resolution_score(v_i, key, "Strong Cadence") > resolution_score(ii_i, key, "Strong Cadence")


@pytest.mark.parametrize("preference", TENSION_LEVELS)
def test_all_tension_preferences_are_accepted(preference):
    validate_progression_preferences(
        start_degree=None,
        end_degree=None,
        tension_preference=preference,
        resolution_preference="Flexible",
        voice_leading_preference="Balanced",
    )


@pytest.mark.parametrize("preference", RESOLUTION_PREFERENCES)
def test_all_resolution_preferences_are_accepted(preference):
    validate_progression_preferences(
        start_degree=None,
        end_degree=None,
        tension_preference="Balanced",
        resolution_preference=preference,
        voice_leading_preference="Balanced",
    )


@pytest.mark.parametrize("preference", VOICE_LEADING_PREFERENCES)
def test_all_voice_leading_preferences_are_accepted(preference):
    validate_progression_preferences(
        start_degree=None,
        end_degree=None,
        tension_preference="Balanced",
        resolution_preference="Flexible",
        voice_leading_preference=preference,
    )


def test_invalid_progression_preferences_are_rejected():
    with pytest.raises(ValueError, match="start_degree"):
        validate_progression_preferences(
            start_degree=8,
            end_degree=None,
            tension_preference="Balanced",
            resolution_preference="Flexible",
            voice_leading_preference="Balanced",
        )
    with pytest.raises(ValueError, match="tension preference"):
        validate_progression_preferences(
            start_degree=None,
            end_degree=None,
            tension_preference="Extreme",
            resolution_preference="Flexible",
            voice_leading_preference="Balanced",
        )
    with pytest.raises(ValueError, match="resolution preference"):
        validate_progression_preferences(
            start_degree=None,
            end_degree=None,
            tension_preference="Balanced",
            resolution_preference="Extreme",
            voice_leading_preference="Balanced",
        )
    with pytest.raises(ValueError, match="voice-leading preference"):
        validate_progression_preferences(
            start_degree=None,
            end_degree=None,
            tension_preference="Balanced",
            resolution_preference="Flexible",
            voice_leading_preference="Extreme",
        )


def test_voice_leading_quality_rewards_common_tones():
    first = build_chord("C", "Maj7")
    connected = build_chord("A", "m7")
    distant = build_chord("F#", "Major")
    assert 0.0 <= voice_leading_quality(first, connected) <= 1.0
    assert 0.0 <= voice_leading_quality(first, distant) <= 1.0
    assert voice_leading_quality(first, connected) > voice_leading_quality(first, distant)


def test_smooth_voice_leading_preference_rewards_connected_progressions():
    first = build_chord("C", "Maj7")
    connected = build_chord("A", "m7")
    distant = build_chord("F#", "Major")
    smooth = (first, connected)
    contrast = (first, distant)
    assert voice_leading_score(smooth, "Smooth") > voice_leading_score(contrast, "Smooth")
    assert voice_leading_score(contrast, "Expressive") > voice_leading_score(smooth, "Expressive")


def test_voice_leading_score_for_single_chord_is_neutral():
    chord = build_chord("C", "Major")
    assert voice_leading_score((chord,), "Smooth") == 0.0
