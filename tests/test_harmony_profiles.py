import pytest

from generator.harmony_profiles import (
    MOOD_PROFILES,
    STYLE_PROFILES,
    combine_profiles,
    get_mood_profile,
    get_style_profile,
    score_chord,
    TEMPLATE_FAMILIES,
)
from music.chord_qualities import CHORD_QUALITIES, DERIVED_CHORD_QUALITIES, build_chord, build_derived_chord
from music.options import MOODS, MUSICAL_CHARACTERS


def test_every_product_mood_has_a_profile():
    assert list(MOOD_PROFILES) == MOODS
    assert all(profile.name in MOODS for profile in MOOD_PROFILES.values())


def test_every_product_style_has_a_profile():
    assert list(STYLE_PROFILES) == MUSICAL_CHARACTERS
    assert all(profile.name in MUSICAL_CHARACTERS for profile in STYLE_PROFILES.values())


def test_all_profile_quality_names_are_known_to_chord_engine():
    known = set(CHORD_QUALITIES) | set(DERIVED_CHORD_QUALITIES)

    for profile in [*MOOD_PROFILES.values(), *STYLE_PROFILES.values()]:
        assert profile.preferred_qualities <= known
        assert profile.avoided_qualities <= known


def test_profiles_have_valid_ranges():
    for profile in [*MOOD_PROFILES.values(), *STYLE_PROFILES.values()]:
        assert 0.0 <= profile.tension <= 1.0
        assert -1.0 <= profile.complexity_bias <= 1.0
        assert profile.preferred_qualities
        assert profile.preferred_families


@pytest.mark.parametrize("mood", MOODS)
def test_each_mood_profile_is_retrievable(mood):
    profile = get_mood_profile(mood)
    assert profile.name == mood


@pytest.mark.parametrize("style", MUSICAL_CHARACTERS)
def test_each_style_profile_is_retrievable(style):
    profile = get_style_profile(style)
    assert profile.name == style


def test_invalid_mood_rejected():
    with pytest.raises(ValueError, match="Unsupported mood"):
        get_mood_profile("Not A Mood")


def test_invalid_style_rejected():
    with pytest.raises(ValueError, match="Unsupported musical character"):
        get_style_profile("Not A Style")


def test_empty_profile_is_neutral():
    profile = combine_profiles([], [])
    assert profile.name == "Neutral"
    assert profile.preferred_qualities == frozenset()
    assert profile.preferred_families == frozenset()
    assert profile.avoided_qualities == frozenset()
    assert profile.tension == 0.40
    assert profile.complexity_bias == 0.0


def test_combining_profiles_is_deterministic_and_deduplicated():
    profile = combine_profiles(["Dreamy", "Dreamy"], ["Neo Soul", "Neo Soul"])
    assert profile.name == "Dreamy + Neo Soul"

    expected = combine_profiles(["Dreamy"], ["Neo Soul"])
    assert profile == expected


def test_combining_multiple_profiles_averages_numeric_preferences():
    dreamy = get_mood_profile("Dreamy")
    neo_soul = get_style_profile("Neo Soul")
    combined = combine_profiles(["Dreamy"], ["Neo Soul"])

    assert combined.tension == pytest.approx((dreamy.tension + neo_soul.tension) / 2)
    assert combined.complexity_bias == pytest.approx(
        (dreamy.complexity_bias + neo_soul.complexity_bias) / 2
    )


def test_combined_profile_unions_harmonic_preferences():
    dreamy = get_mood_profile("Dreamy")
    jazz = get_style_profile("Jazz")
    combined = combine_profiles(["Dreamy"], ["Jazz"])

    assert dreamy.preferred_qualities.issubset(combined.preferred_qualities)
    assert jazz.preferred_qualities.issubset(combined.preferred_qualities)
    assert dreamy.preferred_families.issubset(combined.preferred_families)
    assert jazz.preferred_families.issubset(combined.preferred_families)


def test_score_rewards_explicit_preference():
    profile = get_mood_profile("Dreamy")
    preferred = build_chord("C", "Maj7")
    neutral = build_chord("C", "Major")

    assert score_chord(preferred, profile) > score_chord(neutral, profile)


def test_score_penalizes_explicit_avoidance():
    profile = get_mood_profile("Tense")
    preferred = build_chord("G", "Dominant")
    avoided = build_chord("G", "6/9")

    assert score_chord(preferred, profile) > score_chord(avoided, profile)


def test_complex_profile_can_reward_richer_chords():
    profile = get_style_profile("Jazz")
    simple = build_chord("C", "Major")
    rich = build_derived_chord("C", "Maj7+13")

    assert score_chord(rich, profile) > score_chord(simple, profile)


def test_simple_style_can_favor_simpler_harmony():
    profile = get_style_profile("Pop")
    simple = build_chord("C", "Major")
    altered = build_chord("C", "Altered")

    assert score_chord(simple, profile) > score_chord(altered, profile)


def test_score_is_finite_and_deterministic_for_all_profiles():
    chords = [
        build_chord("C", "Major"),
        build_chord("A", "Minor"),
        build_chord("G", "Dominant"),
        build_chord("D", "m7"),
        build_derived_chord("F", "Maj7+13"),
        build_derived_chord("B", "m7b5"),
        build_chord("C", "Altered"),
        build_chord("E", "Quartal"),
    ]

    for profile in [*MOOD_PROFILES.values(), *STYLE_PROFILES.values()]:
        for chord in chords:
            first = score_chord(chord, profile)
            second = score_chord(chord, profile)
            assert first == second
            assert isinstance(first, float)


def test_every_mood_style_pair_can_be_combined_and_score_common_chords():
    chords = [
        build_chord("C", "Major"),
        build_chord("D", "m7"),
        build_chord("G", "Dominant"),
        build_derived_chord("A", "m7+9"),
        build_chord("F", "Maj7"),
    ]

    for mood in MOODS:
        for style in MUSICAL_CHARACTERS:
            profile = combine_profiles([mood], [style])
            scores = [score_chord(chord, profile) for chord in chords]
            assert len(scores) == len(chords)
            assert all(isinstance(value, float) for value in scores)


def test_every_mood_and_style_profile_has_valid_template_preferences():
    for profile in [*MOOD_PROFILES.values(), *STYLE_PROFILES.values()]:
        families = tuple(family for family, _ in profile.template_preferences)
        weights = tuple(weight for _, weight in profile.template_preferences)
        assert families == tuple(sorted(set(families)))
        assert set(families) <= TEMPLATE_FAMILIES
        assert all(isinstance(weight, float) for weight in weights)
        assert all(weight > 0 for weight in weights)


def test_combined_profile_merges_template_preferences_from_mood_and_style():
    dreamy = get_mood_profile("Dreamy")
    neo_soul = get_style_profile("Neo Soul")
    combined = combine_profiles(["Dreamy"], ["Neo Soul"])

    for family in TEMPLATE_FAMILIES:
        expected = dreamy.template_weight(family) + neo_soul.template_weight(family)
        assert combined.template_weight(family) == pytest.approx(expected)


def test_template_preferences_change_with_mood_and_style():
    dreamy_jazz = combine_profiles(["Dreamy"], ["Neo Soul"])
    dark_cinematic = combine_profiles(["Dark"], ["Cinematic"])

    assert dreamy_jazz.template_weight("jazz") > dark_cinematic.template_weight("jazz")
    assert dark_cinematic.template_weight("cinematic") > dreamy_jazz.template_weight("cinematic")
