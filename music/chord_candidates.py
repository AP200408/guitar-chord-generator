"""Generate context-aware chord candidates from a key and user preferences.

Step 5 sits between the key-aware diatonic chord engine and the future
progression generator.  It does not choose progressions; it answers:

    "For each scale degree, which chord forms are valid candidates for the
     selected chord characteristics and complexity?"

The product-facing chord characteristics remain the values in
``music.options.CHORD_CHARACTERISTICS``.  Contextual extension names such as
``Maj9`` and ``m9`` are implementation details and are returned as canonical
``Chord`` objects.
"""

from __future__ import annotations

from collections.abc import Iterable

from .chord_qualities import build_chord, build_derived_chord
from .key_chords import get_chords_in_key
from .models import Chord, Key
from .notes import pitch_class
from .options import CHORD_CHARACTERISTICS, COMPLEXITIES
from .scales import scale_notes

# The natural seventh quality of each scale degree.  ``None`` means that a
# seventh-extension family is intentionally not inferred for that degree.
NATURAL_SEVENTH_QUALITIES: dict[str, tuple[str | None, ...]] = {
    "Major": ("Maj7", "m7", "m7", "Maj7", "7th", "m7", "m7b5"),
    "Natural Minor": ("m7", "m7b5", "Maj7", "m7", "m7", "Maj7", "7th"),
    "Harmonic Minor": ("mMaj7", "m7b5", "Maj7#5", "m7", "7th", "Maj7", "dim7"),
    "Melodic Minor": ("mMaj7", "m7", "Maj7#5", "7th", "7th", "m7b5", "m7b5"),
}

# Which complexity levels permit common chromatic candidates.  These rules are
# deliberately conservative: Advanced adds idiomatic color; Experimental
# removes most structural restrictions while still requiring a constructible
# chord.
_COMPLEXITY_RANK = {
    "Beginner": 0,
    "Intermediate": 1,
    "Advanced": 2,
    "Experimental": 3,
}

# Explicit base-quality requirements for characteristics that are not simply
# "use the existing diatonic triad".
_REQUIRED_BASE_QUALITIES: dict[str, frozenset[str]] = {
    "Maj7": frozenset({"Major"}),
    "m7": frozenset({"Minor"}),
    "mMaj7": frozenset({"Minor"}),
    "Add9": frozenset({"Major", "Minor"}),
    "6th": frozenset({"Major", "Minor"}),
    "6/9": frozenset({"Major", "Minor"}),
    "Sus": frozenset({"Major", "Minor"}),
    "Dominant": frozenset({"Major"}),
    "7th": frozenset({"Major", "Minor", "Diminished", "Augmented"}),
    "9th": frozenset({"Major", "Minor"}),
    "11th": frozenset({"Major", "Minor"}),
    "13th": frozenset({"Major", "Minor"}),
    "Altered": frozenset({"Major"}),
    "Quartal": frozenset({"Major", "Minor", "Diminished", "Augmented"}),
    "Diminished": frozenset({"Diminished"}),
    "Augmented": frozenset({"Augmented"}),
    "Major": frozenset({"Major"}),
    "Minor": frozenset({"Minor"}),
}

# Internal contextual names that are allowed by the extension resolver.
_EXTENSION_STEPS: dict[str, str] = {
    "9th": "9",
    "11th": "11",
    "13th": "13",
}


def _validate_characteristics(characteristics: Iterable[str]) -> tuple[str, ...]:
    values = tuple(dict.fromkeys(characteristics))
    invalid = [value for value in values if value not in CHORD_CHARACTERISTICS]
    if invalid:
        raise ValueError(
            f"Unsupported chord characteristic(s): {', '.join(invalid)}"
        )
    return values


def _validate_complexity(complexity: str) -> None:
    if complexity not in COMPLEXITIES:
        raise ValueError(
            f"Unsupported complexity: {complexity}. "
            f"Use one of {', '.join(COMPLEXITIES)}"
        )


def _all_notes_in_key(chord: Chord, key: Key) -> bool:
    scale = set(pitch_class(note) for note in scale_notes(key.root_name, key.scale_type))
    return all(pitch_class(note) in scale for note in chord.notes)


def _natural_seventh_quality(key: Key, degree: int) -> str | None:
    return NATURAL_SEVENTH_QUALITIES[key.scale_type][degree - 1]


def _extension_quality_name(
    *,
    base_quality: str,
    seventh_quality: str | None,
    characteristic: str,
) -> str | None:
    """Resolve a generic seventh/extension characteristic contextually."""
    if characteristic == "7th":
        if seventh_quality in {"Maj7", "m7", "mMaj7", "7th", "m7b5", "dim7", "Maj7#5"}:
            return seventh_quality
        return None

    if characteristic in {"9th", "11th", "13th"}:
        if seventh_quality not in {"Maj7", "m7", "mMaj7", "7th", "m7b5", "dim7", "Maj7#5"}:
            return None
        extension = _EXTENSION_STEPS[characteristic]
        return f"{seventh_quality}+{extension}"

    return None


def _build_candidate(
    root: str,
    base_quality: str,
    characteristic: str,
    seventh_quality: str | None,
) -> Chord | None:
    """Build one candidate, or return None when the combination is undefined."""
    if characteristic in {"Major", "Minor", "Diminished", "Augmented", "Dominant", "Maj7", "m7", "mMaj7", "Quartal"}:
        # Explicit product characteristics with a direct quality mapping.
        direct_quality = {
            "Major": "Major",
            "Minor": "Minor",
            "Diminished": "Diminished",
            "Augmented": "Augmented",
            "Dominant": "Dominant",
            "Maj7": "Maj7",
            "m7": "m7",
            "mMaj7": "mMaj7",
            "Quartal": "Quartal",
        }[characteristic]
        return build_chord(root, direct_quality)

    if characteristic == "7th":
        if seventh_quality in {"Maj7", "m7", "mMaj7"}:
            return build_chord(root, seventh_quality)
        if seventh_quality == "7th":
            return build_chord(root, "7th")
        if seventh_quality in {"m7b5", "dim7", "Maj7#5"}:
            return build_derived_chord(root, seventh_quality)
        return None

    if characteristic in {"9th", "11th", "13th"}:
        quality_name = _extension_quality_name(
            base_quality=base_quality,
            seventh_quality=seventh_quality,
            characteristic=characteristic,
        )
        if quality_name is not None:
            return build_derived_chord(root, quality_name)
        return None

    if characteristic == "Add9":
        return build_derived_chord(root, "MajAdd9" if base_quality == "Major" else "mAdd9")

    if characteristic == "6th":
        return build_derived_chord(root, "6" if base_quality == "Major" else "m6")

    if characteristic == "6/9":
        return build_derived_chord(root, "6/9" if base_quality == "Major" else "m6/9")

    if characteristic == "Sus":
        return build_chord(root, "Sus")

    if characteristic == "Altered":
        return build_chord(root, "Altered")

    return None


def _is_structurally_allowed(
    key: Key,
    degree: int,
    base_quality: str,
    characteristic: str,
    complexity: str,
) -> bool:
    """Apply the characteristic compatibility matrix before note-fit testing."""
    minimum_base = _REQUIRED_BASE_QUALITIES[characteristic]
    if base_quality not in minimum_base:
        return False

    rank = _COMPLEXITY_RANK[complexity]

    # Altered harmony is reserved for the dominant scale degree at Advanced+
    # and can be used more freely in Experimental mode.
    if characteristic == "Altered":
        if degree == 5 and rank >= 2:
            return True
        return rank >= 3

    # Quartal voicings are color/voicing choices.  Intermediate and above allow
    # them on all structurally suitable triads; Beginner stays conservative.
    if characteristic == "Quartal":
        return rank >= 1

    # Chromatic replacement triads are an Advanced/Experimental tool.  At lower
    # levels only the actual diatonic triad quality is offered.
    if characteristic in {"Major", "Minor", "Diminished", "Augmented"}:
        if rank >= 2:
            return True
        return base_quality == characteristic

    # Dominant-seventh family is most natural on degree V.  Intermediate allows
    # the common secondary-dominant color only when the resulting notes remain
    # in key; Advanced allows other major-root dominant candidates.
    if characteristic == "Dominant" and rank == 0:
        return degree == 5 and base_quality == "Major"

    if characteristic == "7th":
        return _natural_seventh_quality(key, degree) is not None

    # Everything else is first governed by its base-quality compatibility.
    return True


def get_chord_candidates(
    key: Key,
    degree: int,
    characteristics: Iterable[str],
    complexity: str = "Intermediate",
) -> list[Chord]:
    """Return valid chord candidates for one scale degree.

    Candidates are returned in the caller's characteristic order, with
    duplicate harmonic results removed.  The base diatonic chord itself is
    only returned when its characteristic was requested.
    """
    if not 1 <= degree <= 7:
        raise ValueError("Scale degree must be between 1 and 7")
    _validate_complexity(complexity)
    requested = _validate_characteristics(characteristics)

    base = get_chords_in_key(key)[degree - 1]
    seventh_quality = _natural_seventh_quality(key, degree)

    result: list[Chord] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for characteristic in requested:
        if not _is_structurally_allowed(
            key,
            degree,
            base.quality,
            characteristic,
            complexity,
        ):
            continue

        candidate = _build_candidate(
            base.root,
            base.quality,
            characteristic,
            seventh_quality,
        )
        if candidate is None:
            continue

        # Keep the same Roman numeral as the underlying scale degree.
        candidate = Chord(
            root=candidate.root,
            quality=candidate.quality,
            intervals=candidate.intervals,
            notes=candidate.notes,
            display_name=candidate.display_name,
            roman_numeral=base.roman_numeral,
        )

        in_key = _all_notes_in_key(candidate, key)
        rank = _COMPLEXITY_RANK[complexity]

        # Beginner requires a fully diatonic result. Intermediate does as well
        # for non-structural chromatic colors; Advanced/Experimental permit the
        # documented common/experimental exceptions above.
        if not in_key and characteristic == "Quartal" and rank >= 1:
            pass
        elif not in_key and rank < 2:
            continue
        if not in_key and characteristic == "Altered" and degree != 5 and rank < 3:
            continue

        signature = (candidate.root, candidate.notes)
        if signature in seen:
            continue
        seen.add(signature)
        result.append(candidate)

    return result


def get_chord_candidates_in_key(
    key: Key,
    characteristics: Iterable[str],
    complexity: str = "Intermediate",
) -> dict[str, list[Chord]]:
    """Return candidate chords grouped by Roman numeral for every scale degree."""
    return {
        chord.roman_numeral: get_chord_candidates(
            key,
            degree,
            characteristics,
            complexity,
        )
        for degree, chord in enumerate(get_chords_in_key(key), start=1)
    }
