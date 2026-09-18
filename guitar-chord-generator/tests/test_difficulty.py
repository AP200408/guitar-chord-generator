import pytest

from generator.difficulty import DifficultyRating, calculate_difficulty
from music.chord_qualities import build_chord, build_derived_chord
from music.key_chords import get_chords_in_key
from music.models import Key


def test_rating_display_has_five_slots():
    rating = DifficultyRating(score=3.2, level="Advanced")
    assert len(rating.dots) == 5
    assert rating.display == f"{rating.dots} Advanced"


def test_simple_diatonic_progression_is_low_difficulty():
    key = Key("C", "Normal", "Major")
    chords = tuple(get_chords_in_key(key)[index] for index in (0, 5, 3, 4))
    rating = calculate_difficulty(chords, key)
    assert rating.level in {"Beginner", "Intermediate"}
    assert 1.0 <= rating.score <= 2.8


def test_extended_chords_are_harder_than_basic_triads():
    key = Key("C", "Normal", "Major")
    simple = tuple(get_chords_in_key(key)[index] for index in (0, 5, 3, 4))
    extended = (
        build_derived_chord("C", "Maj7+9"),
        build_derived_chord("A", "m7+9"),
        build_derived_chord("F", "Maj7+11"),
        build_derived_chord("G", "7th+13"),
    )
    extended = tuple(
        chord.__class__(
            root=chord.root,
            quality=chord.quality,
            intervals=chord.intervals,
            notes=chord.notes,
            display_name=chord.display_name,
            roman_numeral=roman,
        )
        for chord, roman in zip(extended, ("I", "vi", "IV", "V"))
    )
    assert calculate_difficulty(extended, key).score > calculate_difficulty(simple, key).score


def test_altered_harmony_is_harder():
    key = Key("C", "Normal", "Major")
    basic = tuple(get_chords_in_key(key)[index] for index in (0, 3, 1, 4))
    altered = (
        build_chord("C", "Altered"),
        build_chord("F", "Altered"),
        build_chord("D", "Altered"),
        build_chord("G", "Altered"),
    )
    assert calculate_difficulty(altered, key).score > calculate_difficulty(basic, key).score


def test_difficulty_is_deterministic():
    key = Key("A", "Normal", "Minor", "Harmonic Minor")
    chords = tuple(get_chords_in_key(key)[index] for index in (0, 3, 4, 0))
    first = calculate_difficulty(chords, key)
    second = calculate_difficulty(chords, key)
    assert first == second


def test_empty_progression_is_rejected():
    key = Key("C", "Normal", "Major")
    with pytest.raises(ValueError, match="empty progression"):
        calculate_difficulty((), key)
