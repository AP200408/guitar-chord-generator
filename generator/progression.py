"""Musically constrained guitar progression generation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
import math
import random

from music.chord_candidates import get_chord_candidates
from music.guitar import GuitarVoicing, find_progression_voicings
from music.key_chords import get_chords_in_key
from music.models import Chord, GeneratorParameters, Key
from music.options import (
    CHORD_CHARACTERISTICS,
    COMPLEXITIES,
    MOODS,
    MUSICAL_CHARACTERS,
)

from .difficulty import DifficultyRating, calculate_difficulty
from .harmony_profiles import HarmonyProfile, combine_profiles, score_chord
from .playing import PlayingRecommendation, recommend_playing_style

# Curated progression shapes. The keys are progression lengths so the user can
# request 2–8 chords without degrading into random degree selection.
MAJOR_TEMPLATES: dict[int, tuple[tuple[int, ...], ...]] = {
    2: (
        (5, 1), (4, 1), (1, 5), (6, 4), (2, 5),
    ),
    3: (
        (2, 5, 1), (1, 6, 4), (6, 4, 1), (1, 4, 5), (4, 5, 1),
    ),
    4: (
        (1, 5, 6, 4), (1, 6, 4, 5), (6, 4, 1, 5), (1, 4, 6, 5),
        (2, 5, 1, 6), (1, 3, 6, 4), (2, 5, 1, 4),
    ),
    5: (
        (1, 5, 6, 4, 5), (6, 4, 1, 5, 1), (1, 6, 4, 2, 5),
        (2, 5, 1, 6, 4), (1, 4, 6, 5, 1),
    ),
    6: (
        (1, 5, 6, 4, 2, 5), (1, 6, 4, 5, 2, 5), (6, 4, 1, 5, 2, 5),
        (2, 5, 1, 6, 4, 5), (1, 4, 6, 2, 5, 1),
    ),
    7: (
        (1, 5, 6, 4, 2, 5, 1), (6, 4, 1, 5, 2, 5, 1),
        (1, 6, 4, 1, 2, 5, 1), (2, 5, 1, 6, 4, 5, 1),
    ),
    8: (
        (1, 5, 6, 4, 2, 5, 1, 4), (1, 6, 4, 5, 2, 5, 1, 4),
        (6, 4, 1, 5, 2, 5, 1, 4), (2, 5, 1, 6, 4, 5, 1, 4),
    ),
}

MINOR_TEMPLATES: dict[int, tuple[tuple[int, ...], ...]] = {
    2: (
        (5, 1), (4, 1), (1, 5), (6, 5), (7, 1),
    ),
    3: (
        (2, 5, 1), (1, 6, 3), (1, 7, 6), (6, 3, 7), (1, 4, 5),
    ),
    4: (
        (1, 6, 3, 7), (1, 7, 6, 5), (1, 6, 4, 5), (1, 4, 6, 5),
        (6, 3, 7, 1), (2, 5, 1, 6), (1, 4, 5, 1),
    ),
    5: (
        (1, 6, 3, 7, 5), (1, 7, 6, 5, 1), (1, 6, 4, 5, 1),
        (6, 3, 7, 1, 5), (2, 5, 1, 6, 4),
    ),
    6: (
        (1, 6, 3, 7, 4, 5), (1, 7, 6, 5, 2, 5), (6, 3, 7, 1, 4, 5),
        (2, 5, 1, 6, 4, 5), (1, 4, 5, 1, 6, 3),
    ),
    7: (
        (1, 6, 3, 7, 4, 5, 1), (1, 7, 6, 5, 2, 5, 1),
        (6, 3, 7, 1, 4, 5, 1), (2, 5, 1, 6, 4, 5, 1),
    ),
    8: (
        (1, 6, 3, 7, 4, 5, 1, 6), (1, 7, 6, 5, 2, 5, 1, 4),
        (6, 3, 7, 1, 4, 5, 1, 6), (2, 5, 1, 6, 4, 5, 1, 7),
    ),
}

STYLE_TEMPLATE_WEIGHTS: dict[str, dict[str, float]] = {
    "Neo Soul": {"jazz": 1.6, "pop": 0.4},
    "Jazz": {"jazz": 2.0, "classic": 0.7},
    "R&B": {"jazz": 1.5, "pop": 0.7},
    "Funk": {"funk": 1.8, "classic": 0.4},
    "Pop": {"pop": 1.8, "classic": 0.7},
    "Blues": {"funk": 1.7, "classic": 0.8},
    "Lo-fi": {"jazz": 1.2, "pop": 0.6},
    "Gospel": {"jazz": 1.6, "classic": 0.8},
    "Acoustic": {"pop": 1.6, "classic": 0.7},
    "Rock": {"classic": 1.6, "funk": 0.9},
    "Cinematic": {"cinematic": 1.8, "classic": 0.7},
}

MOOD_TEMPLATE_WEIGHTS: dict[str, dict[str, float]] = {
    "Happy": {"pop": 1.0, "classic": 0.7},
    "Sad": {"minor": 1.2, "cinematic": 0.8},
    "Dreamy": {"jazz": 1.0, "cinematic": 0.9},
    "Dark": {"minor": 1.5, "cinematic": 1.0},
    "Romantic": {"jazz": 1.1, "pop": 0.7},
    "Mysterious": {"cinematic": 1.4, "minor": 1.0},
    "Tense": {"jazz": 0.9, "cinematic": 1.2},
    "Peaceful": {"pop": 0.9, "classic": 0.8},
    "Nostalgic": {"classic": 1.2, "pop": 0.7},
    "Funky": {"funk": 1.5},
    "Soulful": {"jazz": 1.3, "classic": 0.5},
    "Cinematic": {"cinematic": 1.7},
    "Hopeful": {"pop": 1.2, "classic": 0.7},
    "Aggressive": {"funk": 1.1, "minor": 0.8},
    "Melancholic": {"minor": 1.4, "jazz": 0.8},
}


def _validate_parameters(parameters: GeneratorParameters) -> None:
    if parameters.complexity not in COMPLEXITIES:
        raise ValueError(f"Unsupported complexity: {parameters.complexity}")
    invalid_moods = [m for m in parameters.moods if m not in MOODS]
    if invalid_moods:
        raise ValueError(f"Unsupported mood(s): {', '.join(invalid_moods)}")
    invalid_styles = [s for s in parameters.styles if s not in MUSICAL_CHARACTERS]
    if invalid_styles:
        raise ValueError(f"Unsupported musical character(s): {', '.join(invalid_styles)}")
    invalid_characteristics = [
        c for c in parameters.characteristics if c not in CHORD_CHARACTERISTICS
    ]
    if invalid_characteristics:
        raise ValueError(
            f"Unsupported chord characteristic(s): {', '.join(invalid_characteristics)}"
        )
    if not 2 <= parameters.chords_per_progression <= 8:
        raise ValueError("chords_per_progression must be between 2 and 8")
    if not 1 <= parameters.progression_count <= 8:
        raise ValueError("progression_count must be between 1 and 8")


def _template_family(template: tuple[int, ...], mode: str) -> str:
    if mode == "Minor":
        if 5 in template and template[-1] in {1, 5}:
            return "minor"
        return "cinematic"
    if 2 in template and 5 in template and 1 in template:
        return "jazz"
    if template.count(4) >= 2 or (1 in template and 4 in template and 5 in template):
        return "funk"
    if 6 in template and 4 in template and 1 in template:
        return "pop"
    if template[-1] == 1 and 5 in template:
        return "cinematic"
    return "classic"


def _templates_for_key(key: Key, length: int) -> tuple[tuple[int, ...], ...]:
    bank = MINOR_TEMPLATES if key.mode == "Minor" else MAJOR_TEMPLATES
    return bank[length]


def _template_preference(
    template: tuple[int, ...],
    key: Key,
    moods: tuple[str, ...],
    styles: tuple[str, ...],
) -> float:
    family = _template_family(template, key.mode)
    score = 0.0
    if key.mode == "Minor" and family == "minor":
        score += 1.0
    for style in styles:
        score += STYLE_TEMPLATE_WEIGHTS.get(style, {}).get(family, 0.0)
    for mood in moods:
        score += MOOD_TEMPLATE_WEIGHTS.get(mood, {}).get(family, 0.0)
    if template[-1] == 1:
        score += 0.8
    if 5 in template:
        score += 0.35
    if len(set(template)) >= max(2, len(template) // 2):
        score += 0.2
    return score


def _fallback_candidate(key: Key, degree: int) -> Chord:
    return get_chords_in_key(key)[degree - 1]


def _candidate_pool(
    key: Key,
    degree: int,
    characteristics: tuple[str, ...],
    complexity: str,
) -> list[Chord]:
    candidates = get_chord_candidates(key, degree, characteristics, complexity)
    return candidates if candidates else [_fallback_candidate(key, degree)]


def _progression_signature(chords: tuple[Chord, ...]) -> tuple[str, ...]:
    return tuple(chord.display_name for chord in chords)


def _degree_signature(chords: tuple[Chord, ...]) -> tuple[str | None, ...]:
    return tuple(chord.roman_numeral for chord in chords)


def _transition_score(previous: Chord, current: Chord, key: Key) -> float:
    prev = previous.roman_numeral
    curr = current.roman_numeral
    if not prev or not curr:
        return 0.0
    prev_base = prev.replace("°", "").replace("+", "")
    curr_base = curr.replace("°", "").replace("+", "")
    score = 0.0
    if prev_base in {"V", "v"} and curr_base in {"I", "i"}:
        score += 3.0
    if prev_base in {"ii", "ii°", "iv"} and curr_base in {"V", "v"}:
        score += 1.5
    if prev_base == "VII" and curr_base in {"I", "i"}:
        score += 1.1
    if prev_base == "IV" and curr_base in {"V", "v"}:
        score += 0.9
    if curr_base in {"I", "i"} and prev_base != curr_base:
        score += 0.25
    if previous.root == current.root:
        score -= 0.7
    return score


def _progression_score(
    chords: tuple[Chord, ...],
    profile: HarmonyProfile,
    template: tuple[int, ...],
    key: Key,
    moods: tuple[str, ...],
    styles: tuple[str, ...],
) -> float:
    score = sum(score_chord(chord, profile) for chord in chords)
    for previous, current in zip(chords, chords[1:]):
        score += _transition_score(previous, current, key)
    score += _template_preference(template, key, moods, styles)
    qualities = {chord.quality for chord in chords}
    if len(qualities) == 1:
        score -= 1.0
    elif len(qualities) >= min(3, len(chords)):
        score += 0.4
    if len(set(chord.root for chord in chords)) == 1:
        score -= 1.0
    return round(score, 6)


def _diversity_distance(left: tuple[Chord, ...], right: tuple[Chord, ...]) -> int:
    return sum(a.display_name != b.display_name for a, b in zip(left, right))


def _weighted_index(scores: list[float], rng: random.Random, temperature: float = 0.9) -> int:
    if not scores:
        raise ValueError("scores cannot be empty")
    maximum = max(scores)
    weights = [math.exp((score - maximum) / temperature) for score in scores]
    total = sum(weights)
    pick = rng.random() * total
    running = 0.0
    for index, weight in enumerate(weights):
        running += weight
        if running >= pick:
            return index
    return len(weights) - 1


def _sample_candidate(
    pool: list[Chord],
    profile: HarmonyProfile,
    rng: random.Random,
) -> Chord:
    ranked = sorted(pool, key=lambda c: score_chord(c, profile), reverse=True)
    # Keep the strongest candidates, but intentionally sample among them.
    window = ranked[: min(6, len(ranked))]
    scores = [score_chord(chord, profile) for chord in window]
    return window[_weighted_index(scores, rng)]


@dataclass(frozen=True)
class Progression:
    chords: tuple[Chord, ...]
    roman_numerals: tuple[str, ...]
    score: float
    degrees: tuple[int, ...]
    difficulty: DifficultyRating
    playing: PlayingRecommendation
    voicings: tuple[GuitarVoicing, ...] = ()

    @property
    def display_name(self) -> str:
        return " → ".join(chord.display_name for chord in self.chords)


@dataclass(frozen=True)
class GeneratedProgressions:
    main: Progression
    alternatives: tuple[Progression, ...]

    @property
    def all_progressions(self) -> tuple[Progression, ...]:
        return (self.main, *self.alternatives)


def _build_template_candidates(
    key: Key,
    template: tuple[int, ...],
    parameters: GeneratorParameters,
    profile: HarmonyProfile,
    rng: random.Random,
    trials: int,
) -> list[Progression]:
    pools = [
        _candidate_pool(key, degree, parameters.characteristics, parameters.complexity)
        for degree in template
    ]
    results: list[Progression] = []
    for _ in range(trials):
        chords = tuple(_sample_candidate(pool, profile, rng) for pool in pools)
        score = _progression_score(
            chords, profile, template, key, parameters.moods, parameters.styles
        )
        playing_seed = rng.randrange(1_000_000_000)
        results.append(
            Progression(
                chords=chords,
                roman_numerals=tuple(chord.roman_numeral or "" for chord in chords),
                score=score,
                degrees=template,
                difficulty=calculate_difficulty(chords, key),
                playing=recommend_playing_style(parameters, chords, seed=playing_seed),
            )
        )
    return results


def _select_distinct(
    candidates: list[Progression],
    count: int,
    rng: random.Random,
    progression_length: int,
) -> list[Progression]:
    unique: dict[tuple[str, ...], Progression] = {}
    for candidate in candidates:
        unique.setdefault(_progression_signature(candidate.chords), candidate)
    pool = list(unique.values())
    if not pool:
        raise RuntimeError("No valid progression candidates could be generated")

    pool.sort(key=lambda item: item.score, reverse=True)
    selected: list[Progression] = []
    # Randomly choose among a high-quality band for the main result.
    band_size = min(len(pool), max(8, count * 6))
    main_index = _weighted_index(
        [item.score for item in pool[:band_size]], rng, temperature=1.15
    )
    selected.append(pool.pop(main_index))

    min_distance = max(1, math.ceil(progression_length * 0.4))
    while pool and len(selected) < count:
        eligible = [
            item
            for item in pool
            if all(
                _diversity_distance(item.chords, other.chords) >= min_distance
                for other in selected
            )
        ]
        if not eligible:
            eligible = pool
        # Prefer quality while allowing meaningful variation.
        ranked = sorted(eligible, key=lambda item: item.score, reverse=True)
        window = ranked[: min(len(ranked), max(10, count * 5))]
        chosen = window[_weighted_index([x.score for x in window], rng, temperature=1.05)]
        selected.append(chosen)
        pool.remove(chosen)

    if len(selected) < count:
        # A narrow request can legitimately have fewer unique harmonic results
        # than the requested output count. Never fail the UI: fill the remaining
        # slots from the strongest available candidates. Normal/high-entropy
        # requests should still remain distinct because the unique pool is used
        # first.
        fallback_pool = sorted(unique.values(), key=lambda item: item.score, reverse=True)
        index = 0
        while len(selected) < count:
            selected.append(fallback_pool[index % len(fallback_pool)])
            index += 1
    return selected


def generate_progressions(
    parameters: GeneratorParameters,
    seed: int | None = None,
) -> GeneratedProgressions:
    """Generate the requested number of quality-diverse progressions."""
    _validate_parameters(parameters)
    profile = combine_profiles(parameters.moods, parameters.styles)
    rng = random.Random(seed)
    length = parameters.chords_per_progression
    count = parameters.progression_count
    templates = _templates_for_key(parameters.key, length)

    template_trials = max(12, count * 10)
    all_candidates: list[Progression] = []

    # Sample every curated template, but vary candidate selection inside each
    # template. This gives style/mood influence without collapsing to one answer.
    for template in templates:
        all_candidates.extend(
            _build_template_candidates(
                parameters.key,
                template,
                parameters,
                profile,
                rng,
                template_trials,
            )
        )

    if not all_candidates:
        raise RuntimeError("No valid progression candidates could be generated")

    selected = _select_distinct(all_candidates, count, rng, length)
    selected_with_voicings = [
        replace(item, voicings=find_progression_voicings(item.chords))
        for item in selected
    ]

    return GeneratedProgressions(
        main=selected_with_voicings[0],
        alternatives=tuple(selected_with_voicings[1:]),
    )
