import pytest

from music.keys import (
    HARMONIC_MINOR_ROMANS,
    MAJOR_ROMANS,
    MELODIC_MINOR_ROMANS,
    MINOR_ROMANS,
    NATURAL_MINOR_ROMANS,
    get_diatonic_chords,
    scale_type_for_key,
)
from music.models import Key
from music.notes import pitch_class
from music.scales import SCALE_STEPS, scale_notes


def test_c_major():
    assert get_diatonic_chords(Key('C', 'Normal', 'Major')) == [
        ('I', 'C'), ('ii', 'Dm'), ('iii', 'Em'), ('IV', 'F'), ('V', 'G'), ('vi', 'Am'), ('vii°', 'Bdim')
    ]


def test_c_natural_minor():
    assert get_diatonic_chords(Key('C', 'Normal', 'Minor', 'Natural Minor')) == [
        ('i', 'Cm'), ('ii°', 'Ddim'), ('III', 'Eb'), ('iv', 'Fm'), ('v', 'Gm'), ('VI', 'Ab'), ('VII', 'Bb')
    ]


def test_c_harmonic_minor():
    assert get_diatonic_chords(Key('C', 'Normal', 'Minor', 'Harmonic Minor')) == [
        ('i', 'Cm'), ('ii°', 'Ddim'), ('III+', 'Ebaug'), ('iv', 'Fm'), ('V', 'G'), ('VI', 'Ab'), ('vii°', 'Bdim')
    ]


def test_c_melodic_minor():
    assert get_diatonic_chords(Key('C', 'Normal', 'Minor', 'Melodic Minor')) == [
        ('i', 'Cm'), ('ii', 'Dm'), ('III+', 'Ebaug'), ('IV', 'F'), ('V', 'G'), ('vi°', 'Adim'), ('vii°', 'Bdim')
    ]


def test_f_sharp_major_spelling():
    assert scale_notes('F#', 'Major') == ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#']


def test_b_flat_natural_minor_spelling():
    assert scale_notes('Bb', 'Natural Minor') == ['Bb', 'C', 'Db', 'Eb', 'F', 'Gb', 'Ab']


def test_b_flat_harmonic_minor_spelling():
    assert scale_notes('Bb', 'Harmonic Minor') == ['Bb', 'C', 'Db', 'Eb', 'F', 'Gb', 'A']


def test_c_melodic_minor_spelling():
    assert scale_notes('C', 'Melodic Minor') == ['C', 'D', 'Eb', 'F', 'G', 'A', 'B']


def test_key_scale_type_resolution():
    assert Key('C', 'Normal', 'Major').scale_type == 'Major'
    assert Key('C', 'Normal', 'Minor', 'Natural Minor').scale_type == 'Natural Minor'
    assert Key('C', 'Normal', 'Minor', 'Harmonic Minor').scale_type == 'Harmonic Minor'
    assert Key('C', 'Normal', 'Minor', 'Melodic Minor').scale_type == 'Melodic Minor'


def test_scale_type_for_key():
    assert scale_type_for_key(Key('C', 'Normal', 'Major')) == 'Major'
    assert scale_type_for_key(Key('C', 'Normal', 'Minor', 'Natural Minor')) == 'Natural Minor'
    assert scale_type_for_key(Key('C', 'Normal', 'Minor', 'Harmonic Minor')) == 'Harmonic Minor'
    assert scale_type_for_key(Key('C', 'Normal', 'Minor', 'Melodic Minor')) == 'Melodic Minor'


def test_roman_numerals_are_exact():
    assert MAJOR_ROMANS == ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    assert NATURAL_MINOR_ROMANS == ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
    assert HARMONIC_MINOR_ROMANS == ['i', 'ii°', 'III+', 'iv', 'V', 'VI', 'vii°']
    assert MELODIC_MINOR_ROMANS == ['i', 'ii', 'III+', 'IV', 'V', 'vi°', 'vii°']
    assert MINOR_ROMANS == NATURAL_MINOR_ROMANS


def test_invalid_key_root_rejected():
    with pytest.raises(ValueError, match='Unsupported root'):
        Key('H', 'Normal', 'Major')


def test_invalid_accidental_rejected():
    with pytest.raises(ValueError, match='Unsupported accidental'):
        Key('C', 'DoubleSharp', 'Major')


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match='Unsupported key mode'):
        Key('C', 'Normal', 'Dorian')


def test_major_key_must_use_default_minor_scale_placeholder():
    with pytest.raises(ValueError, match='default Natural Minor placeholder'):
        Key('C', 'Normal', 'Major', 'Harmonic Minor')


@pytest.mark.parametrize('root_name', [
    'A', 'A#', 'Ab',
    'B', 'B#', 'Bb',
    'C', 'C#', 'Cb',
    'D', 'D#', 'Db',
    'E', 'E#', 'Eb',
    'F', 'F#', 'Fb',
    'G', 'G#', 'Gb',
])
@pytest.mark.parametrize('scale_type', list(SCALE_STEPS))
def test_all_supported_root_spellings_and_scales(root_name, scale_type):
    notes = scale_notes(root_name, scale_type)

    assert len(notes) == 7
    assert len({note[0] for note in notes}) == 7

    root_pc = pitch_class(root_name)
    for index, note in enumerate(notes):
        expected_pc = (root_pc + SCALE_STEPS[scale_type][index]) % 12
        assert pitch_class(note) == expected_pc


@pytest.mark.parametrize('root_name, expected_last_note', [
    ('G#', 'F##'),
    ('A#', 'G##'),
    ('E#', 'D##'),
])
def test_double_accidental_scale_spelling(root_name, expected_last_note):
    assert scale_notes(root_name, 'Major')[-1] == expected_last_note


def test_extreme_spelling_preserves_valid_pitch_classes():
    from music.notes import pitch_class
    from music.scales import scale_notes

    notes = scale_notes('G#', 'Harmonic Minor')
    assert len(notes) == 7
    assert all(0 <= pitch_class(note) <= 11 for note in notes)
