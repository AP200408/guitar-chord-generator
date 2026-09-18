import pytest

from generator.playing import (
    TECHNIQUES,
    PlayingRecommendation,
    recommend_playing_style,
)
from music.chord_qualities import build_chord
from music.models import GeneratorParameters, Key
from music.options import MOODS, MUSICAL_CHARACTERS, COMPLEXITIES


def make_params(*, moods=("Dreamy",), styles=("Neo Soul",), complexity="Advanced"):
    return GeneratorParameters(
        key=Key("C", "Normal", "Major"),
        moods=tuple(moods),
        styles=tuple(styles),
        complexity=complexity,
        characteristics=("Maj7", "9th"),
    )


def test_recommendation_returns_expected_type():
    result = recommend_playing_style(make_params(), ())
    assert isinstance(result, PlayingRecommendation)
    assert result.technique in TECHNIQUES
    assert result.pattern
    assert result.reason


def test_dreamy_neo_soul_prefers_fingerstyle_family():
    result = recommend_playing_style(make_params(), ())
    assert result.technique in {"Fingerstyle", "Fingerstyle / Soft Strumming"}


def test_funky_funk_prefers_strumming_family():
    params = make_params(moods=("Funky",), styles=("Funk",), complexity="Intermediate")
    result = recommend_playing_style(params, ())
    assert result.technique in {"Strumming", "Strong Strumming"}


def test_aggressive_rock_prefers_strong_strumming():
    params = make_params(moods=("Aggressive",), styles=("Rock",), complexity="Advanced")
    result = recommend_playing_style(params, ())
    assert result.technique == "Strong Strumming"


def test_peaceful_acoustic_prefers_fingerstyle_family():
    params = make_params(moods=("Peaceful",), styles=("Acoustic",), complexity="Intermediate")
    result = recommend_playing_style(params, ())
    assert result.technique in {"Fingerstyle", "Soft Strumming", "Fingerstyle / Soft Strumming"}


def test_invalid_mood_is_rejected():
    with pytest.raises(ValueError, match="Unsupported mood"):
        recommend_playing_style(make_params(moods=("Nope",)), ())


def test_invalid_style_is_rejected():
    with pytest.raises(ValueError, match="Unsupported musical character"):
        recommend_playing_style(make_params(styles=("Nope",)), ())


def test_invalid_complexity_is_rejected():
    with pytest.raises(ValueError, match="Unsupported complexity"):
        recommend_playing_style(make_params(complexity="Easy"), ())


def test_pattern_is_seed_deterministic():
    params = make_params()
    first = recommend_playing_style(params, (), seed=12)
    second = recommend_playing_style(params, (), seed=12)
    assert first == second


def test_different_seeds_can_change_pattern_without_changing_technique():
    params = make_params()
    first = recommend_playing_style(params, (), seed=0)
    second = recommend_playing_style(params, (), seed=1)
    assert first.technique == second.technique
    assert first.pattern != second.pattern


def test_empty_mood_and_style_are_neutral_and_deterministic():
    params = make_params(moods=(), styles=(), complexity="Intermediate")
    first = recommend_playing_style(params, (), seed=2)
    second = recommend_playing_style(params, (), seed=2)
    assert first == second
    assert first.technique in TECHNIQUES


def test_harmonic_texture_can_adjust_fingerstyle_recommendation():
    params = make_params(moods=("Dreamy",), styles=("Neo Soul",), complexity="Advanced")
    chords = tuple(
        build_chord(root, quality)
        for root, quality in (
            ("C", "Maj7"),
            ("A", "m7"),
            ("F", "Maj7"),
            ("G", "13th"),
        )
    )
    result = recommend_playing_style(params, chords, seed=4)
    assert result.technique in {"Fingerstyle", "Fingerstyle / Soft Strumming"}


@pytest.mark.parametrize("mood", MOODS)
def test_every_product_mood_has_a_recommendation(mood):
    result = recommend_playing_style(make_params(moods=(mood,), styles=()), ())
    assert result.technique in TECHNIQUES
    assert result.pattern


@pytest.mark.parametrize("style", MUSICAL_CHARACTERS)
def test_every_product_style_has_a_recommendation(style):
    result = recommend_playing_style(make_params(moods=(), styles=(style,)), ())
    assert result.technique in TECHNIQUES
    assert result.pattern


@pytest.mark.parametrize("complexity", COMPLEXITIES)
def test_every_complexity_has_a_recommendation(complexity):
    result = recommend_playing_style(make_params(complexity=complexity), ())
    assert result.technique in TECHNIQUES
    assert result.pattern


@pytest.mark.parametrize("mood", MOODS)
@pytest.mark.parametrize("style", MUSICAL_CHARACTERS)
def test_every_mood_style_pair_is_supported(mood, style):
    result = recommend_playing_style(
        make_params(moods=(mood,), styles=(style,), complexity="Intermediate"),
        (),
        seed=3,
    )
    assert result.technique in TECHNIQUES
    assert result.pattern


def test_generated_progression_now_contains_playing_recommendation():
    from generator.progression import generate_progressions

    params = make_params()
    result = generate_progressions(params, seed=11)
    for progression in result.all_progressions:
        assert isinstance(progression.playing, PlayingRecommendation)
        assert progression.playing.technique in TECHNIQUES
        assert progression.playing.pattern
