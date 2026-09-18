"""Seed helpers for reproducible and user-controlled generation."""
from __future__ import annotations

import random
from collections.abc import Callable

MIN_SEED = 0
MAX_SEED = 2_147_483_647


def validate_seed(seed: int) -> int:
    """Validate and normalize a user-facing generation seed."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Seed must be an integer")
    if not MIN_SEED <= seed <= MAX_SEED:
        raise ValueError(f"Seed must be between {MIN_SEED} and {MAX_SEED}")
    return seed


def random_seed() -> int:
    """Return a fresh seed without relying on module-global random state."""
    return random.SystemRandom().randrange(MIN_SEED, MAX_SEED + 1)


def next_seed(seed: int) -> int:
    """Return the next deterministic seed, wrapping at the supported maximum."""
    current = validate_seed(seed)
    return MIN_SEED if current == MAX_SEED else current + 1


def seed_for_action(
    current_seed: int,
    action: str,
    use_fixed_seed: bool,
    random_seed_provider: Callable[[], int] | None = None,
) -> int:
    """Choose the generation seed for a UI action.

    Fixed-seed mode preserves the current seed for Generate and Randomize, while
    Regenerate and Refinement advance it so those actions still create a fresh,
    reproducible result. Non-fixed mode uses a fresh random seed for each action.
    """
    current = validate_seed(current_seed)
    if use_fixed_seed:
        if action in {"regenerate", "refine"}:
            return next_seed(current)
        return current

    provider = random_seed_provider or random_seed
    return validate_seed(provider())
