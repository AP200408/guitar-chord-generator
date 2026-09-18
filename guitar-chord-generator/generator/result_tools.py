"""Presentation and refinement helpers for generated progressions."""
from __future__ import annotations

from dataclasses import replace
import random
from typing import Literal

from music.models import GeneratorParameters
from music.options import MOODS
from .progression import GeneratedProgressions, Progression, generate_progressions

Refinement = Literal["simpler", "complex", "new_progression", "new_mood"]

REFINEMENT_LABELS: dict[Refinement, str] = {
    "simpler": "Make simpler",
    "complex": "Make more complex",
    "new_progression": "New progression",
    "new_mood": "New mood",
}

REFINEMENT_HELP: dict[Refinement, str] = {
    "simpler": "Reduce the selected generation complexity by one level.",
    "complex": "Increase the selected generation complexity by one level.",
    "new_progression": "Keep the current settings and generate a different progression.",
    "new_mood": "Keep the key, style, filters, and harmony controls while changing the mood selection.",
}


def progression_summary(progression: Progression) -> dict[str, object]:
    """Return stable, UI-friendly metadata without changing the progression."""
    return {
        "chords": tuple(chord.display_name for chord in progression.chords),
        "roman_numerals": progression.roman_numerals,
        "degrees": progression.degrees,
        "functions": progression.functions,
        "tensions": progression.tensions,
        "difficulty": progression.difficulty.display,
        "score": progression.score,
    }


def explain_functions(progression: Progression) -> tuple[str, ...]:
    """Describe each chord's harmonic role in concise, user-facing language."""
    explanations = {
        "Tonic": "rest or tonal stability",
        "Predominant": "moves away from the tonic",
        "Dominant": "creates tension toward resolution",
        "Color": "adds harmonic color",
    }
    return tuple(
        f"{roman}: {explanations.get(function, function)}"
        for roman, function in zip(progression.roman_numerals, progression.functions)
    )


def refinement_label(action: Refinement) -> str:
    """Return the stable user-facing label for a refinement action."""
    return REFINEMENT_LABELS[action]


def refinement_help(action: Refinement) -> str:
    """Return the stable user-facing help text for a refinement action."""
    return REFINEMENT_HELP[action]


def refinement_is_available(parameters: GeneratorParameters, action: Refinement) -> bool:
    """Return whether a refinement can make a meaningful parameter change."""
    if action == "simpler":
        return parameters.complexity != "Beginner"
    if action == "complex":
        return parameters.complexity != "Experimental"
    if action in {"new_progression", "new_mood"}:
        return True
    raise ValueError(f"Unsupported refinement action: {action}")


def refine_parameters(
    parameters: GeneratorParameters,
    action: Refinement,
    seed: int | None = None,
) -> GeneratorParameters:
    """Create a safe parameter variant for a result refinement action.

    Refinements intentionally preserve every unrelated generation setting. A
    dedicated seed is used only for selecting a replacement mood so the same
    refinement seed is reproducible in tests and does not affect generation
    randomness itself.
    """
    if action == "simpler":
        complexity = {
            "Experimental": "Advanced",
            "Advanced": "Intermediate",
            "Intermediate": "Beginner",
        }.get(parameters.complexity, "Beginner")
        return replace(parameters, complexity=complexity)

    if action == "complex":
        complexity = {
            "Beginner": "Intermediate",
            "Intermediate": "Advanced",
            "Advanced": "Experimental",
        }.get(parameters.complexity, "Experimental")
        return replace(parameters, complexity=complexity)

    if action == "new_progression":
        return parameters

    if action == "new_mood":
        rng = random.Random(seed)
        current_moods = tuple(parameters.moods)
        available = [mood for mood in MOODS if mood not in current_moods]

        # Preserve the user's approximate mood-selection count whenever
        # possible. If every mood is already selected, reset to one fresh
        # selection so the refinement remains visibly meaningful.
        if available:
            target_count = max(1, min(len(current_moods) or 1, len(available), 2))
            replacement_moods = tuple(rng.sample(available, target_count))
        else:
            replacement_moods = (rng.choice(MOODS),)
            if len(current_moods) == 1 and replacement_moods == current_moods:
                replacement_moods = (MOODS[(MOODS.index(replacement_moods[0]) + 1) % len(MOODS)],)

        return replace(parameters, moods=replacement_moods)

    raise ValueError(f"Unsupported refinement action: {action}")


def regenerate_refinement(
    parameters: GeneratorParameters,
    action: Refinement,
    seed: int | None = None,
) -> GeneratedProgressions:
    """Generate a refinement while preserving all unrelated user settings."""
    return generate_progressions(
        refine_parameters(parameters, action, seed=seed),
        seed=seed,
    )
