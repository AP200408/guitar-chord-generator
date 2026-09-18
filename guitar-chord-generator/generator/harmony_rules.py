"""Functional-harmony, tension, endpoint, and voice-leading rules.

Step 2 keeps the generator focused on progression quality rather than adding a
full harmony editor. The helpers here provide a small, explicit vocabulary for:

- harmonic function awareness,
- target tension levels,
- resolution preferences,
- start/end degree constraints, and
- coarse voice-leading preferences.

All calculations are deterministic and use pitch classes rather than guitar
voicing positions, so the rules stay independent of the later voicing layer.
"""

from __future__ import annotations

from collections.abc import Iterable

from music.models import Chord, Key
from music.notes import pitch_class
from music.options import (
    RESOLUTION_PREFERENCES,
    TENSION_LEVELS,
    VOICE_LEADING_PREFERENCES,
)

FUNCTION_NAMES = ("Tonic", "Predominant", "Dominant", "Color", "Passing")

_MAJOR_FUNCTIONS = {
    1: "Tonic",
    2: "Predominant",
    3: "Color",
    4: "Predominant",
    5: "Dominant",
    6: "Tonic",
    7: "Dominant",
}

_MINOR_FUNCTIONS = {
    1: "Tonic",
    2: "Predominant",
    3: "Color",
    4: "Predominant",
    5: "Dominant",
    6: "Tonic",
    7: "Dominant",
}

_FUNCTION_TENSION = {
    "Tonic": 0.15,
    "Predominant": 0.45,
    "Dominant": 0.85,
    "Color": 0.55,
    "Passing": 0.60,
}
_TARGET_TENSION = {
    "Low": 0.25,
    "Balanced": 0.50,
    "High": 0.75,
}

_FUNCTION_TRANSITIONS = {
    ("Tonic", "Predominant"): 0.70,
    ("Predominant", "Dominant"): 1.25,
    ("Dominant", "Tonic"): 2.40,
    ("Tonic", "Dominant"): 0.45,
    ("Predominant", "Tonic"): 0.25,
    ("Color", "Predominant"): 0.40,
    ("Color", "Dominant"): 0.55,
    ("Color", "Tonic"): 0.30,
    ("Dominant", "Predominant"): -0.20,
    ("Dominant", "Color"): -0.10,
    ("Dominant", "Dominant"): -0.45,
    ("Tonic", "Tonic"): -0.20,
    ("Predominant", "Predominant"): -0.18,
}


def validate_progression_preferences(
    *,
    start_degree: int | None,
    end_degree: int | None,
    tension_preference: str,
    resolution_preference: str,
    voice_leading_preference: str,
) -> None:
    """Validate Step 2 progression controls before generation."""
    for name, degree in (("start_degree", start_degree), ("end_degree", end_degree)):
        if degree is not None and not 1 <= degree <= 7:
            raise ValueError(f"{name} must be between 1 and 7, or None")

    if tension_preference not in TENSION_LEVELS:
        raise ValueError(f"Unsupported tension preference: {tension_preference}")
    if resolution_preference not in RESOLUTION_PREFERENCES:
        raise ValueError(
            f"Unsupported resolution preference: {resolution_preference}"
        )
    if voice_leading_preference not in VOICE_LEADING_PREFERENCES:
        raise ValueError(
            "Unsupported voice-leading preference: "
            f"{voice_leading_preference}"
        )


def degree_function(key: Key, degree: int) -> str:
    """Return the broad harmonic function associated with a scale degree."""
    if not 1 <= degree <= 7:
        raise ValueError("Scale degree must be between 1 and 7")
    mapping = _MINOR_FUNCTIONS if key.mode == "Minor" else _MAJOR_FUNCTIONS
    return mapping[degree]


def chord_function(chord: Chord, key: Key, degree: int | None = None) -> str:
    """Return a chord's broad functional role in the selected key."""
    if degree is None:
        roman = (chord.roman_numeral or "").lower()
        roman_base = roman.replace("°", "").replace("+", "")
        roman_to_degree = {
            "i": 1,
            "ii": 2,
            "iii": 3,
            "iv": 4,
            "v": 5,
            "vi": 6,
            "vii": 7,
        }
        degree = roman_to_degree.get(roman_base)
    if degree is None:
        return "Color"
    return degree_function(key, degree)


def _quality_tension(chord: Chord) -> float:
    """Return a small structural tension modifier for a chord quality."""
    quality = chord.quality
    modifier = 0.0
    if quality in {"Dominant", "7th", "Altered"} or quality.startswith("7th+"):
        modifier += 0.10
    if quality in {"Diminished", "Augmented", "dim7", "Maj7#5"}:
        modifier += 0.15
    if "Quartal" in quality:
        modifier += 0.06
    if quality == "Sus" or "sus" in quality.lower():
        modifier += 0.04
    if len(chord.notes) >= 5:
        modifier += 0.02
    return modifier


def chord_tension(chord: Chord, key: Key, degree: int | None = None) -> float:
    """Estimate harmonic tension on a bounded 0–1 scale."""
    function = chord_function(chord, key, degree)
    value = _FUNCTION_TENSION[function] + _quality_tension(chord)
    return round(max(0.0, min(1.0, value)), 6)


def transition_function_score(previous: Chord, current: Chord, key: Key) -> float:
    """Score one functional transition without relying on subjective labels."""
    previous_function = chord_function(previous, key)
    current_function = chord_function(current, key)
    score = _FUNCTION_TRANSITIONS.get((previous_function, current_function), 0.0)

    if previous.root == current.root:
        score -= 0.55
    if previous_function == "Dominant" and current_function == "Tonic":
        score += 0.35
    return round(score, 6)


def target_tension_score(
    chords: tuple[Chord, ...],
    key: Key,
    preference: str,
) -> float:
    """Reward a progression whose average tension matches the requested level."""
    if not chords:
        return 0.0
    target = _TARGET_TENSION[preference]
    average = sum(chord_tension(chord, key) for chord in chords) / len(chords)
    # 2.0 is intentionally modest so tension guides rather than dominates the
    # chord/style profile and functional-transition terms.
    return round((1.0 - abs(average - target)) * 2.0 - 1.0, 6)


def resolution_score(
    chords: tuple[Chord, ...],
    key: Key,
    preference: str,
) -> float:
    """Score how well the ending reflects the selected resolution preference."""
    if not chords or preference == "Flexible":
        return 0.0

    last_function = chord_function(chords[-1], key)
    score = 0.0
    if preference == "Prefer Tonic":
        score += 1.5 if last_function == "Tonic" else -0.15
    elif preference == "Strong Cadence":
        score += 2.0 if last_function == "Tonic" else -0.50
        if len(chords) >= 2:
            previous_function = chord_function(chords[-2], key)
            if previous_function == "Dominant" and last_function == "Tonic":
                score += 2.0
            elif previous_function == "Predominant":
                score -= 0.15
    return round(score, 6)


def _pitch_distance(left: int, right: int) -> int:
    """Return the smallest pitch-class distance in semitones."""
    distance = abs(left - right) % 12
    return min(distance, 12 - distance)


def voice_leading_quality(previous: Chord, current: Chord) -> float:
    """Estimate local voice-leading smoothness from pitch classes.

    The result is 0–1. Common tones and small pitch-class moves improve the
    value; this deliberately ignores octave/register because those belong to
    the guitar voicing layer.
    """
    previous_pitches = {pitch_class(note) for note in previous.notes}
    current_pitches = {pitch_class(note) for note in current.notes}
    if not previous_pitches or not current_pitches:
        return 0.0

    common_ratio = len(previous_pitches & current_pitches) / max(
        len(previous_pitches), len(current_pitches)
    )
    distances = [
        min(_pitch_distance(current_pc, previous_pc) for previous_pc in previous_pitches)
        for current_pc in current_pitches
    ]
    average_distance = sum(distances) / len(distances)
    movement_ratio = 1.0 - (average_distance / 6.0)
    return round(max(0.0, min(1.0, (0.60 * common_ratio) + (0.40 * movement_ratio))), 6)


def voice_leading_score(
    chords: tuple[Chord, ...],
    preference: str,
) -> float:
    """Score a progression against the requested voice-leading preference."""
    if len(chords) < 2:
        return 0.0

    qualities = [
        voice_leading_quality(previous, current)
        for previous, current in zip(chords, chords[1:])
    ]
    average = sum(qualities) / len(qualities)
    if preference == "Smooth":
        return round((average * 2.0) - 1.0, 6)
    if preference == "Expressive":
        return round(((1.0 - average) * 1.5) - 0.50, 6)
    return round((average - 0.50) * 0.75, 6)


def functional_sequence_score(chords: tuple[Chord, ...], key: Key) -> float:
    """Score functional motion across an entire progression."""
    if len(chords) < 2:
        return 0.0
    return round(
        sum(
            transition_function_score(previous, current, key)
            for previous, current in zip(chords, chords[1:])
        ),
        6,
    )


def degree_choices() -> tuple[int | None, ...]:
    """Return UI-friendly degree choices where ``None`` means any degree."""
    return (None, 1, 2, 3, 4, 5, 6, 7)
