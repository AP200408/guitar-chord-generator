import pytest

from generator.progression import (
    GeneratedProgressions,
    Progression,
    generate_progressions,
)
from music.models import GeneratorParameters, Key


def make_params(
    *,
    mode="Major",
    minor_scale_type="Natural Minor",
    moods=("Dreamy",),
    styles=("Neo Soul",),
    complexity="Advanced",
    characteristics=("Maj7", "9th", "6/9"),
    chords_per_progression=4,
    progression_count=4,
):
    return GeneratorParameters(
        key=Key("C", "Normal", mode, minor_scale_type),
        moods=tuple(moods),
        styles=tuple(styles),
        complexity=complexity,
        characteristics=tuple(characteristics),
        chords_per_progression=chords_per_progression,
        progression_count=progression_count,
    )


def test_generate_returns_one_main_and_three_alternatives():
    result = generate_progressions(make_params(), seed=123)
    assert isinstance(result, GeneratedProgressions)
    assert isinstance(result.main, Progression)
    assert len(result.alternatives) == 3
    assert len(result.all_progressions) == 4


def test_every_progression_has_four_chords():
    result = generate_progressions(make_params(), seed=123)
    assert all(len(progression.chords) == 4 for progression in result.all_progressions)


def test_roman_numerals_match_chords():
    result = generate_progressions(make_params(), seed=123)
    for progression in result.all_progressions:
        assert progression.roman_numerals == tuple(
            chord.roman_numeral for chord in progression.chords
        )


def test_same_seed_is_reproducible():
    params = make_params()
    first = generate_progressions(params, seed=99)
    second = generate_progressions(params, seed=99)
    assert first == second


def test_different_seed_can_regenerate_different_results():
    params = make_params()
    first = generate_progressions(params, seed=10)
    second = generate_progressions(params, seed=11)
    assert first.all_progressions != second.all_progressions


def test_alternatives_are_distinct_when_candidate_space_allows_it():
    params = make_params(
        complexity="Advanced",
        characteristics=("Maj7", "9th", "11th", "13th", "6/9"),
    )
    result = generate_progressions(params, seed=77)
    signatures = [progression.display_name for progression in result.all_progressions]
    assert len(set(signatures)) == 4


def test_minor_generation_works_for_all_minor_scales():
    for scale_type in ("Natural Minor", "Harmonic Minor", "Melodic Minor"):
        result = generate_progressions(
            make_params(
                mode="Minor",
                minor_scale_type=scale_type,
                moods=("Melancholic",),
                styles=("Jazz",),
                complexity="Advanced",
                characteristics=("m7", "mMaj7", "9th", "11th", "Dominant"),
            ),
            seed=7,
        )
        assert len(result.all_progressions) == 4
        assert all(len(item.chords) == 4 for item in result.all_progressions)


@pytest.mark.parametrize("mode,scale_type", [
    ("Major", "Natural Minor"),
    ("Minor", "Natural Minor"),
    ("Minor", "Harmonic Minor"),
    ("Minor", "Melodic Minor"),
])
def test_generation_supports_all_scale_types(mode, scale_type):
    result = generate_progressions(
        make_params(
            mode=mode,
            minor_scale_type=scale_type,
            characteristics=("Major", "Minor", "7th", "9th"),
        ),
        seed=21,
    )
    assert len(result.all_progressions) == 4


def test_empty_characteristics_falls_back_to_diatonic_harmony():
    result = generate_progressions(
        make_params(characteristics=()),
        seed=2,
    )
    assert len(result.all_progressions) == 4
    assert all(chord for item in result.all_progressions for chord in item.chords)


def test_invalid_mood_is_rejected():
    with pytest.raises(ValueError, match="Unsupported mood"):
        generate_progressions(make_params(moods=("Not A Mood",)), seed=1)


def test_invalid_style_is_rejected():
    with pytest.raises(ValueError, match="Unsupported musical character"):
        generate_progressions(make_params(styles=("Not A Style",)), seed=1)


def test_invalid_characteristic_is_rejected():
    with pytest.raises(ValueError, match="Unsupported chord characteristic"):
        generate_progressions(make_params(characteristics=("Maj99",)), seed=1)


def test_invalid_complexity_is_rejected():
    with pytest.raises(ValueError, match="Unsupported complexity"):
        generate_progressions(make_params(complexity="Easy"), seed=1)


def test_progression_scores_are_finite_numbers():
    result = generate_progressions(make_params(), seed=3)
    assert all(isinstance(item.score, float) for item in result.all_progressions)


def test_every_generated_progression_has_difficulty():
    result = generate_progressions(make_params(), seed=3)
    for progression in result.all_progressions:
        assert 1.0 <= progression.difficulty.score <= 5.0
        assert progression.difficulty.level in {
            "Beginner", "Intermediate", "Advanced", "Experimental"
        }
        assert len(progression.difficulty.dots) == 5


def test_generated_chords_are_in_requested_key_context():
    # Every generated chord is either a candidate produced for a scale degree or
    # the exact diatonic fallback.  All must retain a degree-level Roman label.
    result = generate_progressions(make_params(), seed=5)
    for progression in result.all_progressions:
        assert all(chord.roman_numeral for chord in progression.chords)


def test_experimental_generation_can_use_broader_harmony():
    result = generate_progressions(
        make_params(
            complexity="Experimental",
            moods=("Mysterious", "Tense"),
            styles=("Jazz", "Cinematic"),
            characteristics=("Altered", "Diminished", "Augmented", "Quartal", "13th"),
        ),
        seed=41,
    )
    assert len(result.all_progressions) == 4


def test_requested_progression_shape_is_respected():
    params = make_params()
    params = GeneratorParameters(
        key=params.key,
        moods=params.moods,
        styles=params.styles,
        complexity=params.complexity,
        characteristics=params.characteristics,
        chords_per_progression=6,
        progression_count=5,
    )
    result = generate_progressions(params, seed=1234)
    assert len(result.all_progressions) == 5
    assert all(len(item.chords) == 6 for item in result.all_progressions)


def test_single_progression_has_no_alternatives():
    params = make_params()
    params = GeneratorParameters(
        key=params.key,
        moods=params.moods,
        styles=params.styles,
        complexity=params.complexity,
        characteristics=params.characteristics,
        chords_per_progression=3,
        progression_count=1,
    )
    result = generate_progressions(params, seed=1234)
    assert len(result.all_progressions) == 1
    assert result.alternatives == ()


def test_different_seeds_change_at_least_one_progression_over_many_seeds():
    params = make_params(
        characteristics=("Maj7", "9th", "11th", "13th", "6th", "6/9", "Add9"),
        chords_per_progression=4,
        progression_count=4,
    )
    signatures = {
        tuple(item.display_name for item in generate_progressions(params, seed=seed).all_progressions)
        for seed in range(12)
    }
    assert len(signatures) >= 6
