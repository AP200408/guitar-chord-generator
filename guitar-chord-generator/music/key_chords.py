"""Canonical conversion from a Key to diatonic Chord objects."""

from __future__ import annotations

from .chord_qualities import build_chord
from .keys import ROMAN_NUMERALS, TRIAD_QUALITIES, scale_type_for_key
from .models import Chord, Key
from .scales import scale_notes


def get_chords_in_key(key: Key) -> list[Chord]:
    """Return the seven diatonic triads for ``key`` as canonical Chord objects."""
    scale_type = scale_type_for_key(key)
    notes = scale_notes(key.root_name, scale_type)
    romans = ROMAN_NUMERALS[scale_type]
    qualities = TRIAD_QUALITIES[scale_type]

    chords: list[Chord] = []
    for root, quality, roman in zip(notes, qualities, romans):
        chord = build_chord(root, quality)
        chords.append(
            Chord(
                root=chord.root,
                quality=chord.quality,
                intervals=chord.intervals,
                notes=chord.notes,
                display_name=chord.display_name,
                roman_numeral=roman,
            )
        )

    return chords


def get_chord_by_degree(key: Key, degree: int) -> Chord:
    """Return one diatonic triad by scale degree (1 through 7)."""
    if not 1 <= degree <= 7:
        raise ValueError("Scale degree must be between 1 and 7")
    return get_chords_in_key(key)[degree - 1]
