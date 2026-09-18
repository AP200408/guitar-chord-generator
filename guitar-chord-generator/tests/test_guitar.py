import pytest

from music.guitar import (
    STANDARD_TUNING,
    GuitarVoicing,
    find_best_guitar_voicing,
    find_guitar_voicings,
    find_progression_voicings,
)
from music.key_chords import get_chords_in_key
from music.models import Key
from music.chord_qualities import build_chord, build_derived_chord


def test_standard_tuning_is_low_to_high():
    assert STANDARD_TUNING == (("E", 40), ("A", 45), ("D", 50), ("G", 55), ("B", 59), ("E", 64))


def test_c_major_has_playable_voicing():
    chord = build_chord("C", "Major")
    voicing = find_best_guitar_voicing(chord)
    assert isinstance(voicing, GuitarVoicing)
    assert len(voicing.frets) == 6
    assert all(-1 <= fret <= 12 for fret in voicing.frets)
    assert "C" in voicing.covered_notes


def test_cmaj9_has_playable_voicing():
    chord = build_derived_chord("C", "Maj7+9")
    voicing = find_best_guitar_voicing(chord)
    assert "C" in voicing.covered_notes
    assert len(voicing.covered_notes) >= 3


def test_voicing_preserves_chord_name():
    chord = build_chord("A", "m7")
    # build_chord accepts root spelling plus quality; verify returned display.
    voicing = find_best_guitar_voicing(chord)
    assert voicing.chord_name == chord.display_name


def test_multiple_voicings_are_unique():
    chord = build_chord("G", "7th")
    voicings = find_guitar_voicings(chord, limit=5)
    shapes = [v.frets for v in voicings]
    assert len(shapes) == len(set(shapes))


def test_invalid_limit_rejected():
    chord = build_chord("C", "Major")
    with pytest.raises(ValueError):
        find_guitar_voicings(chord, limit=0)


def test_progression_voicings_match_progression_length():
    key = Key("C", "Normal", "Major")
    chords = tuple(get_chords_in_key(key)[:4])
    voicings = find_progression_voicings(chords)
    assert len(voicings) == 4
    assert [v.chord_name for v in voicings] == [c.display_name for c in chords]


def test_voicing_tab_uses_x_for_muted_strings():
    chord = build_chord("C", "Major")
    voicing = find_best_guitar_voicing(chord)
    assert len(voicing.tab.split()) == 6
    assert all(part == "X" or part.isdigit() for part in voicing.tab.split())


@pytest.mark.parametrize("root,quality", [
    ("C", "Major"), ("D", "m7"), ("G", "7th"), ("A", "m9"),
])
def test_representative_voicings_are_constructible(root, quality):
    if quality == "m9":
        chord = build_derived_chord(root, "m7+9")
    else:
        chord = build_chord(root, quality)
    voicing = find_best_guitar_voicing(chord)
    assert voicing.score > 0
