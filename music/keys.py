"""Key-level harmonic metadata and diatonic triad symbols."""

from .models import Key
from .scales import scale_notes

MAJOR_ROMANS = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
NATURAL_MINOR_ROMANS = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']
HARMONIC_MINOR_ROMANS = ['i', 'ii°', 'III+', 'iv', 'V', 'VI', 'vii°']
MELODIC_MINOR_ROMANS = ['i', 'ii', 'III+', 'IV', 'V', 'vi°', 'vii°']

# Backward-compatible alias for earlier code. Natural minor is the plain "Minor" system.
MINOR_ROMANS = NATURAL_MINOR_ROMANS

ROMAN_NUMERALS = {
    'Major': MAJOR_ROMANS,
    'Natural Minor': NATURAL_MINOR_ROMANS,
    'Harmonic Minor': HARMONIC_MINOR_ROMANS,
    'Melodic Minor': MELODIC_MINOR_ROMANS,
}

# Canonical chord-quality names, matching chord_qualities.CHORD_QUALITIES keys.
TRIAD_QUALITIES = {
    'Major': ['Major', 'Minor', 'Minor', 'Major', 'Major', 'Minor', 'Diminished'],
    'Natural Minor': ['Minor', 'Diminished', 'Major', 'Minor', 'Minor', 'Major', 'Major'],
    'Harmonic Minor': ['Minor', 'Diminished', 'Augmented', 'Minor', 'Major', 'Major', 'Diminished'],
    'Melodic Minor': ['Minor', 'Minor', 'Augmented', 'Major', 'Major', 'Diminished', 'Diminished'],
}


def scale_type_for_key(key: Key) -> str:
    """Resolve the concrete scale represented by a Key."""
    return key.scale_type


def get_scale_romans(key: Key) -> list[str]:
    """Return the seven Roman numerals for the key's concrete scale."""
    return list(ROMAN_NUMERALS[scale_type_for_key(key)])


def get_diatonic_chords(key: Key) -> list[tuple[str, str]]:
    """Return legacy (Roman numeral, symbol) tuples for the seven diatonic triads."""
    scale_type = scale_type_for_key(key)
    notes = scale_notes(key.root_name, scale_type)
    romans = ROMAN_NUMERALS[scale_type]
    qualities = TRIAD_QUALITIES[scale_type]

    suffixes = {
        'Major': '',
        'Minor': 'm',
        'Diminished': 'dim',
        'Augmented': 'aug',
    }
    return [(romans[i], notes[i] + suffixes[qualities[i]]) for i in range(7)]
