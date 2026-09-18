"""Authoritative chord-quality definitions and chord construction."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ChordQualityDefinition:
    name: str
    intervals: tuple[str, ...]
    suffix: str
    description: str


CHORD_QUALITIES: dict[str, ChordQualityDefinition] = {
    "Major": ChordQualityDefinition("Major", ("1", "3", "5"), "", "Major triad"),
    "Minor": ChordQualityDefinition("Minor", ("1", "b3", "5"), "m", "Minor triad"),
    "Dominant": ChordQualityDefinition("Dominant", ("1", "3", "5", "b7"), "7", "Dominant seventh chord"),
    "Diminished": ChordQualityDefinition("Diminished", ("1", "b3", "b5"), "dim", "Diminished triad"),
    "Augmented": ChordQualityDefinition("Augmented", ("1", "3", "#5"), "aug", "Augmented triad"),
    "Sus": ChordQualityDefinition("Sus", ("1", "4", "5"), "sus4", "Suspended fourth triad"),
    "Add9": ChordQualityDefinition("Add9", ("1", "3", "5", "9"), "add9", "Major triad with an added ninth"),
    "7th": ChordQualityDefinition("7th", ("1", "3", "5", "b7"), "7", "Dominant seventh chord"),
    "Maj7": ChordQualityDefinition("Maj7", ("1", "3", "5", "7"), "maj7", "Major seventh chord"),
    "m7": ChordQualityDefinition("m7", ("1", "b3", "5", "b7"), "m7", "Minor seventh chord"),
    "mMaj7": ChordQualityDefinition("mMaj7", ("1", "b3", "5", "7"), "mMaj7", "Minor-major seventh chord"),
    "9th": ChordQualityDefinition("9th", ("1", "3", "5", "b7", "9"), "9", "Dominant ninth chord"),
    "11th": ChordQualityDefinition("11th", ("1", "3", "5", "b7", "9", "11"), "11", "Dominant eleventh chord"),
    "13th": ChordQualityDefinition("13th", ("1", "3", "5", "b7", "9", "11", "13"), "13", "Dominant thirteenth chord"),
    "6th": ChordQualityDefinition("6th", ("1", "3", "5", "6"), "6", "Major sixth chord"),
    "6/9": ChordQualityDefinition("6/9", ("1", "3", "5", "6", "9"), "6/9", "Major sixth-nine chord"),
    "Altered": ChordQualityDefinition("Altered", ("1", "3", "b5", "b7", "b9", "#9", "#5"), "7alt", "Altered dominant chord"),
    "Quartal": ChordQualityDefinition("Quartal", ("1", "4", "b7", "b3", "b6"), "quartal", "Quartal chord voicing"),
}



# Internal contextual qualities used when a generic product characteristic
# (e.g. "9th") is applied to a major/minor/ dominant family.  These names are
# intentionally separate from CHORD_QUALITIES because the product exposes the
# characteristic, not every derived spelling.
DERIVED_CHORD_QUALITIES: dict[str, ChordQualityDefinition] = {
    "Maj7+9": ChordQualityDefinition("Maj7+9", ("1", "3", "5", "7", "9"), "maj9", "Major ninth chord"),
    "Maj7+11": ChordQualityDefinition("Maj7+11", ("1", "3", "5", "7", "9", "11"), "maj11", "Major eleventh chord"),
    "Maj7+13": ChordQualityDefinition("Maj7+13", ("1", "3", "5", "7", "9", "11", "13"), "maj13", "Major thirteenth chord"),
    "m7+9": ChordQualityDefinition("m7+9", ("1", "b3", "5", "b7", "9"), "m9", "Minor ninth chord"),
    "m7+11": ChordQualityDefinition("m7+11", ("1", "b3", "5", "b7", "9", "11"), "m11", "Minor eleventh chord"),
    "m7+13": ChordQualityDefinition("m7+13", ("1", "b3", "5", "b7", "9", "11", "13"), "m13", "Minor thirteenth chord"),
    "mMaj7+9": ChordQualityDefinition("mMaj7+9", ("1", "b3", "5", "7", "9"), "mMaj9", "Minor-major ninth chord"),
    "mMaj7+11": ChordQualityDefinition("mMaj7+11", ("1", "b3", "5", "7", "9", "11"), "mMaj11", "Minor-major eleventh chord"),
    "mMaj7+13": ChordQualityDefinition("mMaj7+13", ("1", "b3", "5", "7", "9", "11", "13"), "mMaj13", "Minor-major thirteenth chord"),
    "7th+9": ChordQualityDefinition("7th+9", ("1", "3", "5", "b7", "9"), "9", "Dominant ninth chord"),
    "7th+11": ChordQualityDefinition("7th+11", ("1", "3", "5", "b7", "9", "11"), "11", "Dominant eleventh chord"),
    "7th+13": ChordQualityDefinition("7th+13", ("1", "3", "5", "b7", "9", "11", "13"), "13", "Dominant thirteenth chord"),
    "m7b5": ChordQualityDefinition("m7b5", ("1", "b3", "b5", "b7"), "m7b5", "Half-diminished seventh chord"),
    "m7b5+9": ChordQualityDefinition("m7b5+9", ("1", "b3", "b5", "b7", "9"), "m9b5", "Half-diminished ninth chord"),
    "m7b5+11": ChordQualityDefinition("m7b5+11", ("1", "b3", "b5", "b7", "9", "11"), "m11b5", "Half-diminished eleventh chord"),
    "m7b5+13": ChordQualityDefinition("m7b5+13", ("1", "b3", "b5", "b7", "9", "11", "13"), "m13b5", "Half-diminished thirteenth chord"),
    "dim7": ChordQualityDefinition("dim7", ("1", "b3", "b5", "bb7"), "dim7", "Diminished seventh chord"),
    "dim7+9": ChordQualityDefinition("dim7+9", ("1", "b3", "b5", "bb7", "9"), "dim9", "Diminished ninth chord"),
    "dim7+11": ChordQualityDefinition("dim7+11", ("1", "b3", "b5", "bb7", "9", "11"), "dim11", "Diminished eleventh chord"),
    "dim7+13": ChordQualityDefinition("dim7+13", ("1", "b3", "b5", "bb7", "9", "11", "13"), "dim13", "Diminished thirteenth chord"),
    "Maj7#5": ChordQualityDefinition("Maj7#5", ("1", "3", "#5", "7"), "maj7#5", "Augmented major seventh chord"),
    "Maj7#5+9": ChordQualityDefinition("Maj7#5+9", ("1", "3", "#5", "7", "9"), "maj9#5", "Augmented major ninth chord"),
    "Maj7#5+11": ChordQualityDefinition("Maj7#5+11", ("1", "3", "#5", "7", "9", "11"), "maj11#5", "Augmented major eleventh chord"),
    "Maj7#5+13": ChordQualityDefinition("Maj7#5+13", ("1", "3", "#5", "7", "9", "11", "13"), "maj13#5", "Augmented major thirteenth chord"),
    "mAdd9": ChordQualityDefinition("mAdd9", ("1", "b3", "5", "9"), "madd9", "Minor triad with an added ninth"),
    "MajAdd9": ChordQualityDefinition("MajAdd9", ("1", "3", "5", "9"), "add9", "Major triad with an added ninth"),
    "6": ChordQualityDefinition("6", ("1", "3", "5", "6"), "6", "Major sixth chord"),
    "m6": ChordQualityDefinition("m6", ("1", "b3", "5", "6"), "m6", "Minor sixth chord"),
    "6/9": ChordQualityDefinition("6/9", ("1", "3", "5", "6", "9"), "6/9", "Major sixth-nine chord"),
    "m6/9": ChordQualityDefinition("m6/9", ("1", "b3", "5", "6", "9"), "m6/9", "Minor sixth-nine chord"),
}

_INTERVAL_SEMITONES: dict[str, int] = {
    "1": 0,
    "b2": 1, "2": 2, "#2": 3,
    "b3": 3, "3": 4,
    "4": 5, "#4": 6,
    "b5": 6, "5": 7, "#5": 8,
    "b6": 8, "6": 9, "#6": 10,
    "b7": 10, "bb7": 9, "7": 11,
    "b9": 1, "9": 2, "#9": 3,
    "b11": 4, "11": 5, "#11": 6,
    "b13": 8, "13": 9, "#13": 10,
}

_DEGREE_TO_LETTER_OFFSET = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
_NATURAL_LETTERS = ("C", "D", "E", "F", "G", "A", "B")
_NATURAL_PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

_NOTE_RE = re.compile(r"^([A-G])([#b]{0,3})$")
_INTERVAL_RE = re.compile(r"^([b#]*)(\d+)$")


def _parse_root(root: str) -> tuple[str, int]:
    match = _NOTE_RE.fullmatch(root)
    if not match:
        raise ValueError(f"Unsupported chord root: {root}")

    letter, accidental = match.groups()
    offset = accidental.count('#') - accidental.count('b')
    return letter, (_NATURAL_PITCH[letter] + offset) % 12


def interval_semitones(interval: str) -> int:
    try:
        return _INTERVAL_SEMITONES[interval]
    except KeyError as exc:
        raise ValueError(f"Unsupported interval token: {interval}") from exc


def _interval_degree(interval: str) -> int:
    match = _INTERVAL_RE.fullmatch(interval)
    if not match:
        raise ValueError(f"Unsupported interval token: {interval}")

    number = int(match.group(2))
    if number in {9, 11, 13}:
        number -= 7
    if number not in _DEGREE_TO_LETTER_OFFSET:
        raise ValueError(f"Unsupported interval degree: {interval}")
    return number


def _accidental_from_offset(offset: int) -> str:
    mapping = {-3: 'bbb', -2: 'bb', -1: 'b', 0: '', 1: '#', 2: '##', 3: '###'}
    try:
        return mapping[offset]
    except KeyError as exc:
        raise ValueError(f"Unsupported accidental offset: {offset}") from exc


def _spell_interval(root: str, interval: str) -> str:
    root_letter, root_pc = _parse_root(root)
    degree = _interval_degree(interval)

    root_letter_index = _NATURAL_LETTERS.index(root_letter)
    target_letter = _NATURAL_LETTERS[
        (root_letter_index + _DEGREE_TO_LETTER_OFFSET[degree]) % 7
    ]

    target_pc = (root_pc + interval_semitones(interval)) % 12
    natural_target_pc = _NATURAL_PITCH[target_letter]
    raw_offset = (target_pc - natural_target_pc) % 12
    if raw_offset > 6:
        raw_offset -= 12

    return target_letter + _accidental_from_offset(raw_offset)




def get_derived_chord_quality(name: str) -> ChordQualityDefinition:
    """Return an internal contextual chord-quality definition."""
    try:
        return DERIVED_CHORD_QUALITIES[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported derived chord quality: {name}") from exc


def build_derived_chord(root: str, quality: str):
    """Build an internal contextual chord quality."""
    from .models import Chord

    definition = get_derived_chord_quality(quality)
    _parse_root(root)
    intervals = tuple(interval_semitones(token) for token in definition.intervals)
    notes = tuple(_spell_interval(root, token) for token in definition.intervals)
    return Chord(
        root=root,
        quality=quality,
        intervals=intervals,
        notes=notes,
        display_name=f"{root}{definition.suffix}",
    )

def get_chord_quality(name: str) -> ChordQualityDefinition:
    try:
        return CHORD_QUALITIES[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported chord characteristic: {name}") from exc


def build_chord(root: str, quality: str):
    from .models import Chord

    definition = get_chord_quality(quality)
    _parse_root(root)  # validate first
    intervals = tuple(interval_semitones(token) for token in definition.intervals)
    notes = tuple(_spell_interval(root, token) for token in definition.intervals)

    return Chord(
        root=root,
        quality=quality,
        intervals=intervals,
        notes=notes,
        display_name=f"{root}{definition.suffix}",
    )
