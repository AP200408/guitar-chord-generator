"""Pure helpers for Streamlit parameter state.

No Streamlit imports live here. This keeps parameter randomization and state
construction independently testable and prevents UI execution during tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import random

from music.options import (
    CHORD_CHARACTERISTICS,
    COMPLEXITIES,
    KEY_TYPES,
    MINOR_SCALE_TYPES,
    MOODS,
    MUSICAL_CHARACTERS,
    ROOT_NOTES,
    ACCIDENTALS,
)


@dataclass(frozen=True)
class RandomizedParameters:
    root: str
    accidental: str
    key_type: str
    minor_scale_type: str
    moods: tuple[str, ...]
    styles: tuple[str, ...]
    complexity: str
    characteristics: tuple[str, ...]
    chords_per_progression: int
    progression_count: int


def _sample_nonempty(options: list[str], rng: random.Random, maximum: int) -> tuple[str, ...]:
    if maximum < 1:
        raise ValueError("maximum must be at least 1")
    if not options:
        raise ValueError("options cannot be empty")
    count = rng.randint(1, min(maximum, len(options)))
    return tuple(rng.sample(options, count))


def randomized_parameters(seed: int | None = None) -> RandomizedParameters:
    """Return a valid randomized parameter selection.

    A seed makes the selection deterministic, which is useful for tests while
    normal application calls remain non-deterministic.
    """
    rng = random.Random(seed)
    key_type = rng.choice(KEY_TYPES)
    return RandomizedParameters(
        root=rng.choice(ROOT_NOTES),
        accidental=rng.choice(ACCIDENTALS),
        key_type=key_type,
        minor_scale_type=(
            rng.choice(MINOR_SCALE_TYPES) if key_type == "Minor" else "Natural Minor"
        ),
        moods=_sample_nonempty(MOODS, rng, 2),
        styles=_sample_nonempty(MUSICAL_CHARACTERS, rng, 2),
        complexity=rng.choice(COMPLEXITIES),
        characteristics=_sample_nonempty(CHORD_CHARACTERISTICS, rng, 4),
        chords_per_progression=rng.randint(2, 8),
        progression_count=rng.randint(1, 8),
    )
