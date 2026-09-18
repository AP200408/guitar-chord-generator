import pytest

from generator.filters import active_filter_labels, chord_family, progression_matches_filters
from generator.progression import generate_progressions
from tests.test_step2_integration import make_params


def test_chord_family_classification_covers_core_product_qualities():
    result = generate_progressions(
        make_params(
            characteristics=("Major", "Minor", "7th", "Maj7", "9th", "Sus", "Quartal"),
            progression_count=2,
        ),
        seed=202,
    )
    families = {chord_family(chord) for item in result.all_progressions for chord in item.chords}
    assert families <= {"Triads", "Sevenths", "Extensions", "Color"}
    assert families


def test_required_degrees_are_present_in_every_result():
    result = generate_progressions(
        make_params(required_degrees=(1, 5), progression_count=3),
        seed=123,
    )
    for progression in result.all_progressions:
        assert {1, 5}.issubset(set(progression.degrees))


def test_excluded_degree_is_absent_when_compatible_templates_exist():
    result = generate_progressions(
        make_params(
            chords_per_progression=2,
            excluded_degrees=(1,),
            progression_count=2,
        ),
        seed=123,
    )
    for progression in result.all_progressions:
        assert 1 not in progression.degrees


def test_max_difficulty_filter_rejects_harder_results_and_can_be_satisfied_by_triads():
    result = generate_progressions(
        make_params(
            characteristics=("Major", "Minor"),
            max_difficulty="Beginner",
            progression_count=3,
        ),
        seed=123,
    )
    for progression in result.all_progressions:
        assert progression.difficulty.level == "Beginner"


def test_chord_family_filter_requires_every_chord_to_match_selected_families():
    result = generate_progressions(
        make_params(
            characteristics=("7th", "Maj7", "m7", "mMaj7", "Dominant"),
            chord_families=("Sevenths",),
            progression_count=3,
        ),
        seed=123,
    )
    for progression in result.all_progressions:
        assert {chord_family(chord) for chord in progression.chords} == {"Sevenths"}


def test_filters_default_to_no_filtering_and_preserve_step2_seeded_output():
    params = make_params()
    result = generate_progressions(params, seed=2026)
    assert [item.display_name for item in result.all_progressions] == [
        "Dm9 → G9 → Cmaj7 → Fmaj7",
        "Dm9 → G9 → Cmaj9 → Am9",
        "Cmaj7 → Am9 → Fmaj9 → G9",
        "Cmaj7 → G9 → Am9 → Fmaj9",
    ]
    assert [item.score for item in result.all_progressions] == [
        35.769167,
        32.051666,
        26.3,
        25.753333,
    ]


def test_invalid_filter_values_are_rejected():
    with pytest.raises(ValueError, match="max_difficulty"):
        generate_progressions(make_params(max_difficulty="Impossible"), seed=1)

    with pytest.raises(ValueError, match="chord family"):
        generate_progressions(make_params(chord_families=("Unknown",)), seed=1)

    with pytest.raises(ValueError, match="between 1 and 7"):
        generate_progressions(make_params(required_degrees=(8,)), seed=1)


def test_filter_conflicts_are_rejected():
    with pytest.raises(ValueError, match="both required and excluded"):
        generate_progressions(
            make_params(required_degrees=(1,), excluded_degrees=(1,)),
            seed=1,
        )

    with pytest.raises(ValueError, match="Starting Chord cannot be an excluded degree"):
        generate_progressions(
            make_params(start_degree=1, excluded_degrees=(1,)),
            seed=1,
        )


def test_impossible_filter_request_fails_with_user_actionable_message():
    with pytest.raises(RuntimeError, match="active filters"):
        generate_progressions(
            make_params(
                characteristics=("Maj7", "9th"),
                max_difficulty="Beginner",
                progression_count=2,
            ),
            seed=123,
        )


def test_active_filter_labels_are_stable_and_concise():
    labels = active_filter_labels(
        make_params(
            required_degrees=(1, 5),
            excluded_degrees=(3,),
            max_difficulty="Advanced",
            chord_families=("Sevenths", "Extensions"),
        )
    )
    assert labels == (
        "Required: 1, 5",
        "Excluded: 3",
        "Max difficulty: Advanced",
        "Families: Sevenths, Extensions",
    )
