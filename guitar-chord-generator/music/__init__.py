"""Music domain package for the Guitar Chord Generator."""

from .chord_qualities import build_chord, build_derived_chord, get_chord_quality
from .chord_candidates import get_chord_candidates, get_chord_candidates_in_key
from .key_chords import get_chord_by_degree, get_chords_in_key
from .guitar import GuitarVoicing, find_best_guitar_voicing, find_guitar_voicings, find_progression_voicings
from .keys import get_diatonic_chords
from .models import Chord, GeneratorParameters, Key
from .scales import scale_notes

__all__ = [
    'Chord',
    'GeneratorParameters',
    'Key',
    'build_chord',
    'build_derived_chord',
    'get_chord_quality',
    'get_chords_in_key',
    'get_chord_candidates',
    'get_chord_candidates_in_key',
    'get_chord_by_degree',
    'GuitarVoicing',
    'find_best_guitar_voicing',
    'find_guitar_voicings',
    'find_progression_voicings',
    'get_diatonic_chords',
    'scale_notes',
]
