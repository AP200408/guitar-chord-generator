import pytest

from music.key_chords import get_chord_by_degree, get_chords_in_key
from music.models import Key


def test_c_major_full_chords():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chords_in_key(key)

    assert [(c.roman_numeral, c.display_name) for c in chords] == [
        ('I', 'C'),
        ('ii', 'Dm'),
        ('iii', 'Em'),
        ('IV', 'F'),
        ('V', 'G'),
        ('vi', 'Am'),
        ('vii°', 'Bdim'),
    ]


def test_a_natural_minor_full_chords():
    key = Key(root='A', accidental='Normal', mode='Minor', minor_scale_type='Natural Minor')
    chords = get_chords_in_key(key)

    assert [(c.roman_numeral, c.display_name) for c in chords] == [
        ('i', 'Am'),
        ('ii°', 'Bdim'),
        ('III', 'C'),
        ('iv', 'Dm'),
        ('v', 'Em'),
        ('VI', 'F'),
        ('VII', 'G'),
    ]


def test_a_harmonic_minor_full_chords():
    key = Key(root='A', accidental='Normal', mode='Minor', minor_scale_type='Harmonic Minor')
    chords = get_chords_in_key(key)

    assert [(c.roman_numeral, c.display_name) for c in chords] == [
        ('i', 'Am'),
        ('ii°', 'Bdim'),
        ('III+', 'Caug'),
        ('iv', 'Dm'),
        ('V', 'E'),
        ('VI', 'F'),
        ('vii°', 'G#dim'),
    ]


def test_a_melodic_minor_full_chords():
    key = Key(root='A', accidental='Normal', mode='Minor', minor_scale_type='Melodic Minor')
    chords = get_chords_in_key(key)

    assert [(c.roman_numeral, c.display_name) for c in chords] == [
        ('i', 'Am'),
        ('ii', 'Bm'),
        ('III+', 'Caug'),
        ('IV', 'D'),
        ('V', 'E'),
        ('vi°', 'F#dim'),
        ('vii°', 'G#dim'),
    ]


def test_flat_key_spelling_is_preserved():
    key = Key(root='E', accidental='Flat', mode='Major')
    chords = get_chords_in_key(key)
    assert [c.display_name for c in chords] == ['Eb', 'Fm', 'Gm', 'Ab', 'Bb', 'Cm', 'Ddim']


def test_sharp_key_spelling_is_preserved():
    key = Key(root='F', accidental='Sharp', mode='Major')
    chords = get_chords_in_key(key)
    assert [c.display_name for c in chords] == ['F#', 'G#m', 'A#m', 'B', 'C#', 'D#m', 'E#dim']


def test_canonical_chord_objects_are_used():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chords_in_key(key)

    assert chords[0].quality == 'Major'
    assert chords[1].quality == 'Minor'
    assert chords[6].quality == 'Diminished'
    assert chords[0].notes == ('C', 'E', 'G')
    assert chords[1].notes == ('D', 'F', 'A')
    assert chords[6].notes == ('B', 'D', 'F')


def test_chord_by_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert get_chord_by_degree(key, 1).display_name == 'C'
    assert get_chord_by_degree(key, 5).display_name == 'G'
    assert get_chord_by_degree(key, 7).display_name == 'Bdim'


@pytest.mark.parametrize('degree', [0, 8, -1, 10])
def test_invalid_degree_rejected(degree):
    key = Key(root='C', accidental='Normal', mode='Major')
    with pytest.raises(ValueError, match='between 1 and 7'):
        get_chord_by_degree(key, degree)


def test_all_key_chords_have_roman_numerals():
    key = Key(root='C', accidental='Normal', mode='Minor', minor_scale_type='Harmonic Minor')
    chords = get_chords_in_key(key)
    assert all(chord.roman_numeral for chord in chords)
    assert len(chords) == 7


@pytest.mark.parametrize('root_name, scale_type', [
    ('G#', 'Harmonic Minor'),
    ('A#', 'Major'),
    ('E#', 'Major'),
    ('Db', 'Harmonic Minor'),
])
def test_key_chords_support_complex_key_spelling(root_name, scale_type):
    if root_name[1:] == '#':
        root, accidental = root_name[0], 'Sharp'
    elif root_name[1:] == 'b':
        root, accidental = root_name[0], 'Flat'
    else:
        root, accidental = root_name, 'Normal'

    mode = 'Major' if scale_type == 'Major' else 'Minor'
    minor_scale_type = 'Natural Minor' if mode == 'Major' else scale_type
    chords = get_chords_in_key(
        Key(root, accidental, mode, minor_scale_type)
    )

    assert len(chords) == 7
    assert all(chord.roman_numeral for chord in chords)
