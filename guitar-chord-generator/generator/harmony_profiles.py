"""Formal mood/style harmony profiles and candidate scoring.

Each product mood and musical character has an explicit, validated harmonic
profile.  A combined profile carries both chord-vocabulary preferences and
curated progression-family preferences into the progression generator.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Iterable

from music.models import Chord
from music.options import MOODS, MUSICAL_CHARACTERS


@dataclass(frozen=True)
class HarmonyProfile:
    """A normalized description of harmonic preferences."""

    name: str
    preferred_qualities: frozenset[str]
    preferred_families: frozenset[str]
    avoided_qualities: frozenset[str]
    tension: float  # 0.0 = relaxed, 1.0 = highly tense
    complexity_bias: float  # -1.0 = simple, +1.0 = complex
    template_preferences: tuple[tuple[str, float], ...] = ()

    def template_weight(self, family: str) -> float:
        """Return the profile weight for one curated progression family."""
        for name, weight in self.template_preferences:
            if name == family:
                return weight
        return 0.0


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

MOOD_PROFILES: dict[str, HarmonyProfile] = {
    "Happy": HarmonyProfile(
        "Happy",
        frozenset({"Major", "6th", "6/9", "Add9", "Maj7", "m7"}),
        frozenset({"major", "sixth", "major_seventh", "add_nine"}),
        frozenset({"Diminished", "Altered", "mMaj7"}),
        0.20,
        -0.15,
    ),
    "Sad": HarmonyProfile(
        "Sad",
        frozenset({"Minor", "m7", "mMaj7", "m6", "m6/9", "Maj7"}),
        frozenset({"minor", "minor_seventh", "minor_major_seventh", "sixth", "major_seventh"}),
        frozenset({"Altered", "Diminished"}),
        0.48,
        0.10,
    ),
    "Dreamy": HarmonyProfile(
        "Dreamy",
        frozenset({"Maj7", "Add9", "6/9", "m7", "9th", "11th", "Quartal"}),
        frozenset({"major_seventh", "add_nine", "sixth_nine", "minor_seventh", "extended", "quartal"}),
        frozenset({"Diminished", "Altered"}),
        0.30,
        0.35,
    ),
    "Dark": HarmonyProfile(
        "Dark",
        frozenset({"Minor", "m7", "mMaj7", "Diminished", "Altered", "Sus"}),
        frozenset({"minor", "minor_seventh", "minor_major_seventh", "diminished", "altered", "suspended"}),
        frozenset({"6/9"}),
        0.72,
        0.40,
    ),
    "Romantic": HarmonyProfile(
        "Romantic",
        frozenset({"Maj7", "Add9", "9th", "m7", "6/9", "m6"}),
        frozenset({"major_seventh", "add_nine", "extended", "minor_seventh", "sixth_nine", "sixth"}),
        frozenset({"Diminished", "Altered"}),
        0.35,
        0.30,
    ),
    "Mysterious": HarmonyProfile(
        "Mysterious",
        frozenset({"mMaj7", "Diminished", "Augmented", "Sus", "Altered", "Quartal"}),
        frozenset({"minor_major_seventh", "diminished", "augmented", "suspended", "altered", "quartal"}),
        frozenset({"6th"}),
        0.76,
        0.55,
    ),
    "Tense": HarmonyProfile(
        "Tense",
        frozenset({"Dominant", "Altered", "Diminished", "Augmented", "Sus"}),
        frozenset({"dominant", "altered", "diminished", "augmented", "suspended"}),
        frozenset({"6/9"}),
        0.90,
        0.45,
    ),
    "Peaceful": HarmonyProfile(
        "Peaceful",
        frozenset({"Major", "Maj7", "Add9", "6th", "6/9", "m7"}),
        frozenset({"major", "major_seventh", "add_nine", "sixth", "sixth_nine", "minor_seventh"}),
        frozenset({"Altered", "Diminished"}),
        0.12,
        -0.20,
    ),
    "Nostalgic": HarmonyProfile(
        "Nostalgic",
        frozenset({"6th", "6/9", "Maj7", "m7", "Add9", "7th"}),
        frozenset({"sixth", "sixth_nine", "major_seventh", "minor_seventh", "add_nine", "dominant"}),
        frozenset({"Altered"}),
        0.28,
        0.10,
    ),
    "Funky": HarmonyProfile(
        "Funky",
        frozenset({"Dominant", "7th", "Sus", "m7", "9th", "13th"}),
        frozenset({"dominant", "suspended", "minor_seventh", "extended"}),
        frozenset({"mMaj7", "Diminished"}),
        0.48,
        0.28,
    ),
    "Soulful": HarmonyProfile(
        "Soulful",
        frozenset({"Maj7", "m7", "9th", "11th", "13th", "6/9", "Add9"}),
        frozenset({"major_seventh", "minor_seventh", "extended", "sixth_nine", "add_nine"}),
        frozenset({"Diminished"}),
        0.42,
        0.58,
    ),
    "Cinematic": HarmonyProfile(
        "Cinematic",
        frozenset({"Minor", "Maj7", "mMaj7", "Sus", "Diminished", "Augmented", "Quartal"}),
        frozenset({"minor", "major_seventh", "minor_major_seventh", "suspended", "diminished", "augmented", "quartal"}),
        frozenset({"6/9"}),
        0.62,
        0.62,
    ),
    "Hopeful": HarmonyProfile(
        "Hopeful",
        frozenset({"Major", "Maj7", "Add9", "6th", "6/9", "9th"}),
        frozenset({"major", "major_seventh", "add_nine", "sixth", "sixth_nine", "extended"}),
        frozenset({"Altered", "Diminished"}),
        0.22,
        0.15,
    ),
    "Aggressive": HarmonyProfile(
        "Aggressive",
        frozenset({"Dominant", "7th", "Altered", "Diminished", "Augmented", "Sus"}),
        frozenset({"dominant", "altered", "diminished", "augmented", "suspended"}),
        frozenset({"6/9", "Add9"}),
        0.94,
        0.48,
    ),
    "Melancholic": HarmonyProfile(
        "Melancholic",
        frozenset({"Minor", "m7", "mMaj7", "m6", "m6/9", "Maj7", "11th"}),
        frozenset({"minor", "minor_seventh", "minor_major_seventh", "sixth", "major_seventh", "extended"}),
        frozenset({"Altered"}),
        0.58,
        0.30,
    ),
}

STYLE_PROFILES: dict[str, HarmonyProfile] = {
    "Neo Soul": HarmonyProfile(
        "Neo Soul",
        frozenset({"Maj7", "m7", "9th", "11th", "13th", "6/9", "Add9", "Sus"}),
        frozenset({"major_seventh", "minor_seventh", "extended", "sixth_nine", "add_nine", "suspended"}),
        frozenset({"Diminished"}),
        0.43,
        0.72,
    ),
    "Jazz": HarmonyProfile(
        "Jazz",
        frozenset({"Maj7", "m7", "9th", "11th", "13th", "Altered", "Diminished"}),
        frozenset({"major_seventh", "minor_seventh", "extended", "altered", "diminished"}),
        frozenset(),
        0.58,
        0.85,
    ),
    "R&B": HarmonyProfile(
        "R&B",
        frozenset({"Maj7", "m7", "9th", "11th", "13th", "6/9", "Add9"}),
        frozenset({"major_seventh", "minor_seventh", "extended", "sixth_nine", "add_nine"}),
        frozenset({"Diminished", "Altered"}),
        0.40,
        0.62,
    ),
    "Funk": HarmonyProfile(
        "Funk",
        frozenset({"Dominant", "7th", "9th", "13th", "Sus", "m7"}),
        frozenset({"dominant", "extended", "suspended", "minor_seventh"}),
        frozenset({"mMaj7", "Diminished"}),
        0.55,
        0.35,
    ),
    "Pop": HarmonyProfile(
        "Pop",
        frozenset({"Major", "Minor", "7th", "Add9", "Sus", "6th"}),
        frozenset({"major", "minor", "dominant", "add_nine", "suspended", "sixth"}),
        frozenset({"Altered", "Quartal", "mMaj7"}),
        0.22,
        -0.28,
    ),
    "Blues": HarmonyProfile(
        "Blues",
        frozenset({"Dominant", "7th", "9th", "13th", "m7"}),
        frozenset({"dominant", "extended", "minor_seventh"}),
        frozenset({"mMaj7", "Quartal"}),
        0.52,
        0.20,
    ),
    "Lo-fi": HarmonyProfile(
        "Lo-fi",
        frozenset({"m7", "Maj7", "9th", "6/9", "Add9", "11th"}),
        frozenset({"minor_seventh", "major_seventh", "extended", "sixth_nine", "add_nine"}),
        frozenset({"Altered", "Diminished"}),
        0.28,
        0.48,
    ),
    "Gospel": HarmonyProfile(
        "Gospel",
        frozenset({"Maj7", "m7", "9th", "11th", "13th", "Dominant", "6/9"}),
        frozenset({"major_seventh", "minor_seventh", "extended", "dominant", "sixth_nine"}),
        frozenset(),
        0.49,
        0.70,
    ),
    "Acoustic": HarmonyProfile(
        "Acoustic",
        frozenset({"Major", "Minor", "Add9", "Sus", "6th", "6/9", "m7"}),
        frozenset({"major", "minor", "add_nine", "suspended", "sixth", "sixth_nine", "minor_seventh"}),
        frozenset({"Altered", "Quartal"}),
        0.18,
        -0.10,
    ),
    "Rock": HarmonyProfile(
        "Rock",
        frozenset({"Major", "Minor", "7th", "Dominant", "Sus", "Add9"}),
        frozenset({"major", "minor", "dominant", "suspended", "add_nine"}),
        frozenset({"mMaj7", "Quartal"}),
        0.45,
        -0.05,
    ),
    "Cinematic": HarmonyProfile(
        "Cinematic",
        frozenset({"Minor", "Maj7", "mMaj7", "Sus", "Diminished", "Augmented", "Quartal"}),
        frozenset({"minor", "major_seventh", "minor_major_seventh", "suspended", "diminished", "augmented", "quartal"}),
        frozenset({"6/9"}),
        0.66,
        0.64,
    ),
}


# Curated progression-family vocabulary used by the generator. Keeping these
# preferences on the harmony profiles prevents style/mood logic from being
# split across separate generation modules.
TEMPLATE_FAMILIES = frozenset({
    "jazz",
    "pop",
    "funk",
    "classic",
    "cinematic",
    "minor",
})

_STYLE_TEMPLATE_PREFERENCES: dict[str, dict[str, float]] = {
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

_MOOD_TEMPLATE_PREFERENCES: dict[str, dict[str, float]] = {
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


def _attach_template_preferences(
    profiles: dict[str, HarmonyProfile],
    preferences: dict[str, dict[str, float]],
) -> dict[str, HarmonyProfile]:
    """Return profiles with validated, immutable template preferences."""
    enriched: dict[str, HarmonyProfile] = {}
    for name, profile in profiles.items():
        weights = preferences.get(name, {})
        unknown = set(weights) - TEMPLATE_FAMILIES
        if unknown:
            raise ValueError(
                f"Unsupported template family in profile {name!r}: {sorted(unknown)}"
            )
        enriched[name] = replace(
            profile,
            template_preferences=tuple(sorted(weights.items())),
        )
    return enriched


MOOD_PROFILES = _attach_template_preferences(MOOD_PROFILES, _MOOD_TEMPLATE_PREFERENCES)
STYLE_PROFILES = _attach_template_preferences(STYLE_PROFILES, _STYLE_TEMPLATE_PREFERENCES)


def get_mood_profile(mood: str) -> HarmonyProfile:
    """Return the validated harmony profile for one product mood."""
    try:
        return MOOD_PROFILES[mood]
    except KeyError as exc:
        raise ValueError(f"Unsupported mood: {mood}") from exc


def get_style_profile(style: str) -> HarmonyProfile:
    """Return the validated harmony profile for one musical character."""
    try:
        return STYLE_PROFILES[style]
    except KeyError as exc:
        raise ValueError(f"Unsupported musical character: {style}") from exc


def _quality_family(chord: Chord) -> set[str]:
    """Normalize a chord quality into broad harmonic families."""
    quality = chord.quality
    suffix = chord.display_name[len(chord.root):]
    families: set[str] = set()

    if quality == "Major":
        families.add("major")
    if quality == "Minor":
        families.add("minor")
    if quality == "Dominant" or quality == "7th" or quality.startswith("7th+"):
        families.add("dominant")
    if quality in {"m7", "m7b5"} or quality.startswith("m7+") or quality.startswith("m7b5+"):
        families.add("minor_seventh")
    if quality == "Maj7" or quality.startswith("Maj7+") or quality == "Maj7#5" or quality.startswith("Maj7#5+"):
        families.add("major_seventh")
    if quality == "mMaj7" or quality.startswith("mMaj7+"):
        families.add("minor_major_seventh")
    if "6/9" in quality:
        families.add("sixth_nine")
    elif quality in {"6th", "6", "m6"}:
        families.add("sixth")
    if quality in {"Add9", "MajAdd9", "mAdd9"}:
        families.add("add_nine")
    if quality in {"9th", "11th", "13th"} or "+9" in quality or "+11" in quality or "+13" in quality:
        families.add("extended")
    if quality == "Sus":
        families.add("suspended")
    if quality == "Diminished" or quality.startswith("dim") or "m7b5" in quality:
        families.add("diminished")
    if quality == "Augmented" or quality.startswith("Maj7#5"):
        families.add("augmented")
    if quality == "Altered":
        families.add("altered")
    if quality == "Quartal":
        families.add("quartal")

    # Fallbacks based on rendered suffix make the scorer robust to future
    # quality names that follow the established notation.
    if suffix.endswith("sus4"):
        families.add("suspended")
    return families


def combine_profiles(
    moods: Iterable[str],
    styles: Iterable[str],
) -> HarmonyProfile:
    """Combine multiple mood/style profiles into one normalized profile."""
    mood_values = tuple(dict.fromkeys(moods))
    style_values = tuple(dict.fromkeys(styles))

    for mood in mood_values:
        if mood not in MOODS:
            raise ValueError(f"Unsupported mood: {mood}")
    for style in style_values:
        if style not in MUSICAL_CHARACTERS:
            raise ValueError(f"Unsupported musical character: {style}")

    profiles = [get_mood_profile(value) for value in mood_values]
    profiles.extend(get_style_profile(value) for value in style_values)

    if not profiles:
        return HarmonyProfile(
            "Neutral",
            frozenset(),
            frozenset(),
            frozenset(),
            0.40,
            0.0,
        )

    preferred_qualities = frozenset().union(*(profile.preferred_qualities for profile in profiles))
    preferred_families = frozenset().union(*(profile.preferred_families for profile in profiles))
    avoided_qualities = frozenset().union(*(profile.avoided_qualities for profile in profiles))
    tension = sum(profile.tension for profile in profiles) / len(profiles)
    complexity_bias = sum(profile.complexity_bias for profile in profiles) / len(profiles)

    template_scores: dict[str, float] = {}
    for profile in profiles:
        for family, weight in profile.template_preferences:
            template_scores[family] = template_scores.get(family, 0.0) + weight
    template_preferences = tuple(
        sorted(
            (family, round(weight, 6))
            for family, weight in template_scores.items()
            if weight
        )
    )

    name_parts = (*mood_values, *style_values)
    return HarmonyProfile(
        " + ".join(name_parts),
        preferred_qualities,
        preferred_families,
        avoided_qualities,
        tension,
        complexity_bias,
        template_preferences,
    )


def score_chord(chord: Chord, profile: HarmonyProfile) -> float:
    """Score a chord from the perspective of a combined harmony profile.

    The scale is intentionally bounded to a small, interpretable range.
    Positive scores are preferred; negative scores are disfavored.
    """
    score = 0.0
    families = _quality_family(chord)

    if chord.quality in profile.preferred_qualities:
        score += 4.0
    if chord.quality in profile.avoided_qualities:
        score -= 4.0

    score += 2.0 * len(families.intersection(profile.preferred_families))

    # Complexity bias rewards extended/custom qualities for complex profiles
    # and slightly favors foundational triads for simpler profiles.
    note_count = len(chord.notes)
    if profile.complexity_bias > 0:
        score += min(note_count - 3, 4) * profile.complexity_bias
    elif profile.complexity_bias < 0:
        score -= max(note_count - 3, 0) * abs(profile.complexity_bias)

    # A small tension alignment term: broad chord-family tension is estimated
    # from structural families, not from subjective audio claims.
    tension_families = {"dominant", "altered", "diminished", "augmented"}
    chord_tension = min(len(families.intersection(tension_families)) / 2.0, 1.0)
    score += (chord_tension - profile.tension) * 0.5

    return round(score, 6)
