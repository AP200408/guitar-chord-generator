import pytest

from music.chord_qualities import CHORD_QUALITIES, build_chord, get_chord_quality, interval_semitones
from music.options import CHORD_CHARACTERISTICS


def test_every_product_characteristic_has_definition():
    assert list(CHORD_QUALITIES) == CHORD_CHARACTERISTICS


def test_major_chord():
    chord = build_chord('C', 'Major')
    assert chord.intervals == (0, 4, 7)
    assert chord.notes == ('C', 'E', 'G')
    assert chord.display_name == 'C'


def test_minor_chord():
    chord = build_chord('A', 'Minor')
    assert chord.intervals == (0, 3, 7)
    assert chord.notes == ('A', 'C', 'E')
    assert chord.display_name == 'Am'


def test_dominant_and_seventh_are_same_structure():
    dominant = build_chord('G', 'Dominant')
    seventh = build_chord('G', '7th')
    assert dominant.intervals == (0, 4, 7, 10)
    assert dominant.notes == ('G', 'B', 'D', 'F')
    assert seventh.intervals == dominant.intervals
    assert seventh.notes == dominant.notes
    assert dominant.display_name == 'G7'
    assert seventh.display_name == 'G7'


def test_diminished_chord():
    chord = build_chord('B', 'Diminished')
    assert chord.intervals == (0, 3, 6)
    assert chord.notes == ('B', 'D', 'F')
    assert chord.display_name == 'Bdim'


def test_augmented_chord():
    chord = build_chord('C', 'Augmented')
    assert chord.intervals == (0, 4, 8)
    assert chord.notes == ('C', 'E', 'G#')
    assert chord.display_name == 'Caug'


def test_sus_is_sus4():
    chord = build_chord('D', 'Sus')
    assert chord.intervals == (0, 5, 7)
    assert chord.notes == ('D', 'G', 'A')
    assert chord.display_name == 'Dsus4'


def test_add9():
    chord = build_chord('C', 'Add9')
    assert chord.intervals == (0, 4, 7, 2)
    assert chord.notes == ('C', 'E', 'G', 'D')
    assert chord.display_name == 'Cadd9'


def test_major_seventh_spelling():
    chord = build_chord('C', 'Maj7')
    assert chord.intervals == (0, 4, 7, 11)
    assert chord.notes == ('C', 'E', 'G', 'B')
    assert chord.display_name == 'Cmaj7'


def test_minor_seventh_spelling():
    chord = build_chord('A', 'm7')
    assert chord.intervals == (0, 3, 7, 10)
    assert chord.notes == ('A', 'C', 'E', 'G')
    assert chord.display_name == 'Am7'


def test_minor_major_seventh_spelling():
    chord = build_chord('A', 'mMaj7')
    assert chord.intervals == (0, 3, 7, 11)
    assert chord.notes == ('A', 'C', 'E', 'G#')
    assert chord.display_name == 'AmMaj7'


def test_ninth():
    chord = build_chord('G', '9th')
    assert chord.intervals == (0, 4, 7, 10, 2)
    assert chord.notes == ('G', 'B', 'D', 'F', 'A')
    assert chord.display_name == 'G9'


def test_eleventh():
    chord = build_chord('G', '11th')
    assert chord.intervals == (0, 4, 7, 10, 2, 5)
    assert chord.notes == ('G', 'B', 'D', 'F', 'A', 'C')
    assert chord.display_name == 'G11'


def test_thirteenth():
    chord = build_chord('G', '13th')
    assert chord.intervals == (0, 4, 7, 10, 2, 5, 9)
    assert chord.notes == ('G', 'B', 'D', 'F', 'A', 'C', 'E')
    assert chord.display_name == 'G13'


def test_sixth():
    chord = build_chord('C', '6th')
    assert chord.intervals == (0, 4, 7, 9)
    assert chord.notes == ('C', 'E', 'G', 'A')
    assert chord.display_name == 'C6'


def test_six_nine():
    chord = build_chord('C', '6/9')
    assert chord.intervals == (0, 4, 7, 9, 2)
    assert chord.notes == ('C', 'E', 'G', 'A', 'D')
    assert chord.display_name == 'C6/9'


def test_altered_dominant():
    chord = build_chord('C', 'Altered')
    assert chord.intervals == (0, 4, 6, 10, 1, 3, 8)
    assert chord.notes == ('C', 'E', 'Gb', 'Bb', 'Db', 'D#', 'G#')
    assert chord.display_name == 'C7alt'


def test_quartal():
    chord = build_chord('C', 'Quartal')
    assert chord.intervals == (0, 5, 10, 3, 8)
    assert chord.notes == ('C', 'F', 'Bb', 'Eb', 'Ab')
    assert chord.display_name == 'Cquartal'


def test_extended_note_spelling_handles_double_accidentals():
    chord = build_chord('C#', 'Maj7')
    assert chord.notes == ('C#', 'E#', 'G#', 'B#')


def test_double_sharp_root_is_supported():
    chord = build_chord('F##', 'Major')
    assert chord.notes == ('F##', 'A##', 'C##')


def test_double_flat_root_is_supported():
    chord = build_chord('Bbb', 'Major')
    assert chord.notes == ('Bbb', 'Db', 'Fb')


def test_flat_root_spelling():
    chord = build_chord('Db', 'm7')
    assert chord.notes == ('Db', 'Fb', 'Ab', 'Cb')


def test_interval_validation():
    assert interval_semitones('1') == 0
    assert interval_semitones('b3') == 3
    assert interval_semitones('3') == 4
    assert interval_semitones('b7') == 10
    assert interval_semitones('9') == 2


def test_unknown_quality_rejected():
    with pytest.raises(ValueError, match='Unsupported chord characteristic'):
        get_chord_quality('NotAChord')


def test_unknown_interval_rejected():
    with pytest.raises(ValueError, match='Unsupported interval'):
        interval_semitones('b14')


def test_unknown_root_rejected():
    with pytest.raises(ValueError, match='Unsupported chord root'):
        build_chord('H', 'Major')


def test_triple_accidental_chord_spelling_is_supported():
    chord = build_chord('E#', 'Altered')
    assert chord.notes
    assert all(note[0] in 'ABCDEFG' for note in chord.notes)
