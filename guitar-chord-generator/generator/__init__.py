"""Generation-layer helpers for the Guitar Chord Generator."""

from .difficulty import DifficultyRating, calculate_difficulty
from .harmony_profiles import (
    HarmonyProfile,
    MOOD_PROFILES,
    STYLE_PROFILES,
    combine_profiles,
    get_mood_profile,
    get_style_profile,
    score_chord,
)
from .playing import PlayingRecommendation, recommend_playing_style
from .progression import GeneratedProgressions, Progression, generate_progressions

__all__ = [
    "DifficultyRating",
    "calculate_difficulty",
    "HarmonyProfile",
    "MOOD_PROFILES",
    "STYLE_PROFILES",
    "combine_profiles",
    "get_mood_profile",
    "get_style_profile",
    "score_chord",
    "Progression",
    "GeneratedProgressions",
    "generate_progressions",
    "PlayingRecommendation",
    "recommend_playing_style",
]
