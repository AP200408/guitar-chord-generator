"""Pure helpers for Step 4 progression filtering.

The filters are intentionally small and deterministic so they can be applied
inside the generator and tested without importing Streamlit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from music.models import Chord, GeneratorParameters
from music.options import CHORD_FAMILIES as OPTION_CHORD_FAMILIES, COMPLEXITIES

if TYPE_CHECKING:
    from generator.progression import Progression

DIFFICULTY_FILTERS = ("Any", *COMPLEXITIES)
CHORD_FAMILIES = tuple(OPTION_CHORD_FAMILIES)

_DIFFICULTY_RANK = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
    "Experimental": 3,
}

# Explicit families for the product's constructed chord qualities.
_TRIAD_QUALITIES = frozenset({"Major", "Minor", "Diminished", "Augmented"})
_SEVENTH_QUALITIES = frozenset(
    {"Dominant", "7th", "Maj7", "m7", "mMaj7", "m7b5", "dim7", "Maj7#5"}
)
_COLOR_QUALITIES = frozenset({"Sus", "Altered", "Quartal"})
_EXTENSION_QUALITIES = frozenset(
    {
        "Add9",
        "9th",
        "11th",
        "13th",
        "6th",
        "6/9",
        "mAdd9",
        "MajAdd9",
        "m6",
        "m6/9",
        "6",
    }
)


def chord_family(chord: Chord) -> str:
    """Return the user-facing family for a generated chord quality."""
    quality = chord.quality
    if quality in _COLOR_QUALITIES:
        return "Color"
    if quality in _TRIAD_QUALITIES:
        return "Triads"
    if quality in _SEVENTH_QUALITIES:
        return "Sevenths"
    if quality in _EXTENSION_QUALITIES or "+" in quality:
        return "Extensions"

    # Defensive fallback: contextual qualities not yet explicitly listed are
    # treated as extensions when they contain 9/11/13 information; otherwise
    # the safest classification is Color rather than silently allowing them in
    # a more specific family filter.
    if any(token in quality for token in ("9", "11", "13", "6")):
        return "Extensions"
    return "Color"


def progression_matches_filters(
    progression: Progression,
    parameters: GeneratorParameters,
) -> bool:
    """Return whether one generated progression satisfies all Step 4 filters."""
    degrees = tuple(progression.degrees)
    degree_set = set(degrees)

    if parameters.required_degrees and not set(parameters.required_degrees).issubset(degree_set):
        return False
    if parameters.excluded_degrees and degree_set.intersection(parameters.excluded_degrees):
        return False

    if parameters.max_difficulty != "Any":
        maximum_rank = _DIFFICULTY_RANK[parameters.max_difficulty]
        if _DIFFICULTY_RANK[progression.difficulty.level] > maximum_rank:
            return False

    if parameters.chord_families:
        families = {chord_family(chord) for chord in progression.chords}
        if not families.issubset(set(parameters.chord_families)):
            return False

    return True


def active_filter_labels(parameters: GeneratorParameters) -> tuple[str, ...]:
    """Return concise labels suitable for the result header."""
    labels: list[str] = []
    if parameters.required_degrees:
        labels.append("Required: " + ", ".join(f"{degree}" for degree in parameters.required_degrees))
    if parameters.excluded_degrees:
        labels.append("Excluded: " + ", ".join(f"{degree}" for degree in parameters.excluded_degrees))
    if parameters.max_difficulty != "Any":
        labels.append(f"Max difficulty: {parameters.max_difficulty}")
    if parameters.chord_families:
        labels.append("Families: " + ", ".join(parameters.chord_families))
    return tuple(labels)
