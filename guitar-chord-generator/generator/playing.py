"""Mood/style-aware guitar playing recommendations.

Step 9 maps the selected mood, musical character, complexity, and the generated
harmonic texture to a simple, immediately playable recommendation.  It does not
attempt to model guitar voicings or audio playback; those belong to later steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from music.models import Chord, GeneratorParameters
from music.options import COMPLEXITIES, MOODS, MUSICAL_CHARACTERS


TECHNIQUES = (
    "Strumming",
    "Fingerstyle",
    "Soft Strumming",
    "Strong Strumming",
    "Fingerstyle / Soft Strumming",
)

# Relative preferences.  Scores are intentionally interpretable and bounded.
_MOOD_TECHNIQUE_WEIGHTS: dict[str, dict[str, float]] = {
    "Happy": {"Strumming": 1.4, "Soft Strumming": 0.4},
    "Sad": {"Fingerstyle": 1.4, "Soft Strumming": 0.7},
    "Dreamy": {"Fingerstyle": 1.6, "Soft Strumming": 1.0},
    "Dark": {"Fingerstyle": 1.0, "Strong Strumming": 0.8},
    "Romantic": {"Fingerstyle": 1.3, "Soft Strumming": 1.0},
    "Mysterious": {"Fingerstyle": 1.3, "Soft Strumming": 0.8},
    "Tense": {"Strong Strumming": 1.3, "Fingerstyle": 0.7},
    "Peaceful": {"Fingerstyle": 1.5, "Soft Strumming": 1.0},
    "Nostalgic": {"Soft Strumming": 1.3, "Fingerstyle": 1.0},
    "Funky": {"Strumming": 1.8, "Strong Strumming": 1.0},
    "Soulful": {"Fingerstyle / Soft Strumming": 1.5, "Soft Strumming": 0.9},
    "Cinematic": {"Fingerstyle": 1.4, "Strong Strumming": 0.8},
    "Hopeful": {"Strumming": 1.1, "Fingerstyle": 0.8},
    "Aggressive": {"Strong Strumming": 1.9, "Strumming": 1.0},
    "Melancholic": {"Fingerstyle": 1.6, "Soft Strumming": 0.9},
}

_STYLE_TECHNIQUE_WEIGHTS: dict[str, dict[str, float]] = {
    "Neo Soul": {"Fingerstyle / Soft Strumming": 2.2, "Soft Strumming": 0.8},
    "Jazz": {"Fingerstyle": 1.2, "Soft Strumming": 0.8},
    "R&B": {"Soft Strumming": 1.4, "Fingerstyle": 1.1},
    "Funk": {"Strumming": 1.8, "Strong Strumming": 0.9},
    "Pop": {"Strumming": 1.4, "Soft Strumming": 0.7},
    "Blues": {"Strumming": 1.1, "Fingerstyle": 0.9},
    "Lo-fi": {"Fingerstyle": 1.4, "Soft Strumming": 1.0},
    "Gospel": {"Strumming": 1.0, "Fingerstyle / Soft Strumming": 1.0},
    "Acoustic": {"Fingerstyle": 1.2, "Soft Strumming": 1.1},
    "Rock": {"Strong Strumming": 1.7, "Strumming": 1.3},
    "Cinematic": {"Fingerstyle": 1.4, "Strong Strumming": 0.7},
}

_COMPLEXITY_TECHNIQUE_BONUS: dict[str, dict[str, float]] = {
    "Beginner": {"Strumming": 0.25, "Soft Strumming": 0.20, "Fingerstyle": -0.10},
    "Intermediate": {"Fingerstyle": 0.10, "Strumming": 0.05, "Soft Strumming": 0.05},
    "Advanced": {"Fingerstyle": 0.25, "Fingerstyle / Soft Strumming": 0.25},
    "Experimental": {"Fingerstyle": 0.20, "Fingerstyle / Soft Strumming": 0.25},
}

# Patterns are intentionally concise and directly playable rather than being a
# pattern editor. They are strings for now so the later audio layer can map them
# to timing/events without changing the recommendation contract.
_PATTERNS: dict[str, tuple[str, ...]] = {
    "Strumming": (
        "↓ ↓↑ ↑↓↑",
        "↓ ↑ ↓↑ ↓↑",
        "↓ ↓ ↑ ↑ ↓ ↑",
    ),
    "Soft Strumming": (
        "↓   ↓↑   ↑↓",
        "↓  ↑  ↓↑  ↑",
        "↓   ↓   ↑↓↑",
    ),
    "Strong Strumming": (
        "↓ ↓ ↑ ↓ ↑",
        "↓ ↓↑ ↓ ↓↑",
        "↓ ↓ ↓↑ ↓↑",
    ),
    "Fingerstyle": (
        "Bass → G → B → e → B → G",
        "Bass → B → G → e → G → B",
        "Bass → G → e → B → G → e",
    ),
    "Fingerstyle / Soft Strumming": (
        "Bass → G → B → e → B → G",
        "↓   G → B → e → B → G",
        "Bass → G → B → e  +  ↓↑",
    ),
}


def _validate_inputs(
    moods: Iterable[str],
    styles: Iterable[str],
    complexity: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    mood_values = tuple(dict.fromkeys(moods))
    style_values = tuple(dict.fromkeys(styles))

    invalid_moods = [mood for mood in mood_values if mood not in MOODS]
    if invalid_moods:
        raise ValueError(f"Unsupported mood(s): {', '.join(invalid_moods)}")

    invalid_styles = [style for style in style_values if style not in MUSICAL_CHARACTERS]
    if invalid_styles:
        raise ValueError(f"Unsupported musical character(s): {', '.join(invalid_styles)}")

    if complexity not in COMPLEXITIES:
        raise ValueError(f"Unsupported complexity: {complexity}")

    return mood_values, style_values


def _technique_scores(
    moods: tuple[str, ...],
    styles: tuple[str, ...],
    complexity: str,
) -> dict[str, float]:
    scores = {technique: 0.0 for technique in TECHNIQUES}

    for mood in moods:
        for technique, weight in _MOOD_TECHNIQUE_WEIGHTS[mood].items():
            scores[technique] += weight

    for style in styles:
        for technique, weight in _STYLE_TECHNIQUE_WEIGHTS[style].items():
            scores[technique] += weight

    for technique, weight in _COMPLEXITY_TECHNIQUE_BONUS[complexity].items():
        scores[technique] += weight

    # Empty mood/style is neutral.  Provide a small default ordering so the
    # recommendation is deterministic rather than dependent on dict internals.
    if not moods and not styles:
        scores["Fingerstyle"] += 0.1
        scores["Strumming"] += 0.1

    return scores


def _texture_adjustment(technique: str, chords: tuple[Chord, ...]) -> float:
    """Adjust technique slightly from the actual harmonic texture."""
    if not chords:
        return 0.0

    average_notes = sum(len(chord.notes) for chord in chords) / len(chords)
    extended_ratio = sum(len(chord.notes) >= 5 for chord in chords) / len(chords)
    altered_ratio = sum(
        chord.quality == "Altered" or "Quartal" in chord.quality
        for chord in chords
    ) / len(chords)

    adjustment = 0.0
    if technique in {"Fingerstyle", "Fingerstyle / Soft Strumming"}:
        adjustment += max(0.0, average_notes - 4.0) * 0.10
        adjustment += extended_ratio * 0.15
    if technique == "Strong Strumming":
        adjustment += altered_ratio * 0.10
    return adjustment


def _pattern_index(seed_value: int | None, count: int) -> int:
    if count <= 0:
        raise ValueError("Pattern collection cannot be empty")
    if seed_value is None:
        return 0
    return abs(seed_value) % count


@dataclass(frozen=True)
class PlayingRecommendation:
    """A concise recommendation for how to play the generated progression."""

    technique: str
    pattern: str
    reason: str

    @property
    def display(self) -> str:
        return f"{self.technique} · {self.pattern}"


def recommend_playing_style(
    parameters: GeneratorParameters,
    chords: tuple[Chord, ...] | list[Chord] = (),
    *,
    seed: int | None = None,
) -> PlayingRecommendation:
    """Recommend one technique and one simple pattern for a progression."""
    moods, styles = _validate_inputs(
        parameters.moods,
        parameters.styles,
        parameters.complexity,
    )
    chord_sequence = tuple(chords)

    scores = _technique_scores(moods, styles, parameters.complexity)
    for technique in TECHNIQUES:
        scores[technique] += _texture_adjustment(technique, chord_sequence)

    # Stable tie-breaking follows product-friendly specificity: explicit
    # combined techniques first, then fingerstyle, then soft/regular/strong.
    tie_order = {
        "Fingerstyle / Soft Strumming": 0,
        "Fingerstyle": 1,
        "Soft Strumming": 2,
        "Strumming": 3,
        "Strong Strumming": 4,
    }
    technique = max(
        TECHNIQUES,
        key=lambda value: (scores[value], -tie_order[value]),
    )

    patterns = _PATTERNS[technique]
    pattern = patterns[_pattern_index(seed, len(patterns))]

    mood_text = moods[0] if len(moods) == 1 else " + ".join(moods[:2])
    style_text = styles[0] if len(styles) == 1 else " + ".join(styles[:2])

    if mood_text and style_text:
        reason = f"Chosen for {mood_text} mood with {style_text} character."
    elif mood_text:
        reason = f"Chosen for the {mood_text} mood."
    elif style_text:
        reason = f"Chosen for the {style_text} character."
    else:
        reason = "Balanced default recommendation."

    return PlayingRecommendation(
        technique=technique,
        pattern=pattern,
        reason=reason,
    )
