"""Difficulty analysis for generated guitar chord progressions.

The V1 difficulty score describes *harmonic* difficulty only.  Guitar
fingering/playability is intentionally excluded until the guitar-voicing layer
exists.  The result is deterministic for the same chord sequence and key.
"""

from __future__ import annotations

from dataclasses import dataclass

from music.models import Chord, Key
from music.notes import pitch_class
from music.scales import scale_notes


# Intrinsic harmonic complexity of the chord quality.  The weights are kept
# centralized so later tuning does not require changing the calculation logic.
_QUALITY_WEIGHT: dict[str, float] = {
    "Major": 1.0,
    "Minor": 1.0,
    "Sus": 1.2,
    "Diminished": 2.7,
    "Augmented": 2.7,
    "Add9": 1.6,
    "MajAdd9": 1.6,
    "mAdd9": 1.8,
    "6th": 1.6,
    "6": 1.6,
    "m6": 1.8,
    "6/9": 1.9,
    "m6/9": 2.1,
    "Dominant": 2.0,
    "7th": 2.0,
    "Maj7": 2.0,
    "m7": 2.1,
    "mMaj7": 2.6,
    "m7b5": 2.7,
    "dim7": 3.2,
    "Maj7#5": 3.2,
    "9th": 2.6,
    "11th": 2.9,
    "13th": 3.2,
    "Maj7+9": 2.6,
    "Maj7+11": 3.0,
    "Maj7+13": 3.3,
    "m7+9": 2.8,
    "m7+11": 3.1,
    "m7+13": 3.4,
    "mMaj7+9": 3.1,
    "mMaj7+11": 3.4,
    "mMaj7+13": 3.7,
    "7th+9": 2.6,
    "7th+11": 2.9,
    "7th+13": 3.2,
    "m7b5+9": 3.1,
    "m7b5+11": 3.4,
    "m7b5+13": 3.7,
    "dim7+9": 3.6,
    "dim7+11": 3.9,
    "dim7+13": 4.1,
    "Maj7#5+9": 3.6,
    "Maj7#5+11": 3.9,
    "Maj7#5+13": 4.1,
    "Altered": 4.4,
    "Quartal": 3.8,
}


@dataclass(frozen=True)
class DifficultyRating:
    """Deterministic harmonic difficulty result on a five-point scale."""

    score: float
    level: str

    @property
    def dots(self) -> str:
        """Return a compact five-dot display for the UI."""
        filled = max(1, min(5, int(round(self.score))))
        return "●" * filled + "○" * (5 - filled)

    @property
    def display(self) -> str:
        return f"{self.dots} {self.level}"


_LEVELS = (
    (1.8, "Beginner"),
    (2.8, "Intermediate"),
    (3.8, "Advanced"),
    (5.0, "Experimental"),
)


def _quality_weight(chord: Chord) -> float:
    """Return intrinsic harmonic complexity for a chord quality."""
    if chord.quality in _QUALITY_WEIGHT:
        return _QUALITY_WEIGHT[chord.quality]

    # Defensive fallback for future contextual qualities: complexity grows with
    # the number of notes but stays bounded rather than failing generation.
    note_count = len(chord.notes)
    return min(4.0, 0.8 + (0.55 * max(0, note_count - 3)))


def _chromatic_fraction(chords: tuple[Chord, ...], key: Key) -> float:
    """Measure how many generated chord tones lie outside the selected scale."""
    scale_pcs = {
        pitch_class(note)
        for note in scale_notes(key.root_name, key.scale_type)
    }
    total = sum(len(chord.notes) for chord in chords)
    if total == 0:
        return 0.0
    chromatic = sum(
        1
        for chord in chords
        for note in chord.notes
        if pitch_class(note) not in scale_pcs
    )
    return chromatic / total


def _movement_complexity(chords: tuple[Chord, ...]) -> float:
    """Estimate harmonic movement complexity from Roman-degree changes."""
    if len(chords) < 2:
        return 0.0

    changes = 0
    distinctive = set()
    for previous, current in zip(chords, chords[1:]):
        prev = previous.roman_numeral or previous.root
        curr = current.roman_numeral or current.root
        distinctive.add(prev)
        distinctive.add(curr)
        if prev != curr:
            changes += 1

    change_ratio = changes / (len(chords) - 1)
    variety = min(1.0, len(distinctive) / len(chords))
    return (0.6 * change_ratio) + (0.4 * variety)


def calculate_difficulty(chords: tuple[Chord, ...] | list[Chord], key: Key) -> DifficultyRating:
    """Calculate deterministic harmonic difficulty for a progression.

    The score is intentionally independent of the user's selected Complexity
    parameter. Complexity influences *generation*; this function evaluates the
    result that was actually produced.
    """
    sequence = tuple(chords)
    if not sequence:
        raise ValueError("Cannot calculate difficulty for an empty progression")

    average_quality = sum(_quality_weight(chord) for chord in sequence) / len(sequence)
    quality_component = (average_quality - 1.0) / 3.4

    average_notes = sum(len(chord.notes) for chord in sequence) / len(sequence)
    note_component = min(1.0, max(0.0, (average_notes - 3.0) / 4.0))

    chromatic_component = _chromatic_fraction(sequence, key)
    movement_component = _movement_complexity(sequence)

    # Weighted normalized score. Each component is in [0, 1].
    normalized = (
        (0.55 * quality_component)
        + (0.15 * note_component)
        + (0.20 * chromatic_component)
        + (0.10 * movement_component)
    )

    score = 1.0 + (4.0 * normalized)
    score = round(max(1.0, min(5.0, score)), 2)

    for upper_bound, level in _LEVELS:
        if score <= upper_bound:
            return DifficultyRating(score=score, level=level)

    return DifficultyRating(score=5.0, level="Experimental")
