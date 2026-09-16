"""Playable standard-tuning guitar voicings for generated chords."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from functools import lru_cache

from .models import Chord, GuitarVoicing
from .notes import NATURAL_PITCH, parse_note, pitch_class

# Low E -> high E. MIDI numbers keep fret/pitch calculations unambiguous.
STANDARD_TUNING: tuple[tuple[str, int], ...] = (
    ("E", 40), ("A", 45), ("D", 50), ("G", 55), ("B", 59), ("E", 64)
)
MAX_FRET = 12
OPEN = 0
MUTED = -1


def _fret_note(tuning_midi: int, fret: int) -> int:
    return tuning_midi + fret


def _candidate_frets(chord: Chord, string_index: int) -> list[int]:
    tuning_midi = STANDARD_TUNING[string_index][1]
    chord_pcs = {pitch_class(note) for note in chord.notes}
    return [
        fret
        for fret in range(MAX_FRET + 1)
        if _fret_note(tuning_midi, fret) % 12 in chord_pcs
    ]


def _midi_name(midi: int, preferred_notes: tuple[str, ...]) -> str:
    target_pc = midi % 12
    for name in preferred_notes:
        if pitch_class(name) == target_pc:
            return name
    # Defensive fallback; should only occur for impossible coverage queries.
    naturals = tuple(NATURAL_PITCH)
    names = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}
    return names[target_pc]


def _shape_notes(chord: Chord, frets: tuple[int, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for index, fret in enumerate(frets):
        if fret == MUTED:
            continue
        midi = _fret_note(STANDARD_TUNING[index][1], fret)
        names.append(_midi_name(midi, chord.notes))
    return tuple(names)


def _covered_note_names(chord: Chord, played_notes: tuple[str, ...]) -> tuple[str, ...]:
    played_pcs = {pitch_class(note) for note in played_notes}
    return tuple(note for note in chord.notes if pitch_class(note) in played_pcs)


def _difficulty(frets: tuple[int, ...]) -> str:
    fretted = [f for f in frets if f > 0]
    if not fretted:
        return "Beginner"
    span = max(fretted) - min(fretted)
    count = len(fretted)
    if span <= 2 and count <= 4:
        return "Beginner"
    if span <= 4 and count <= 5:
        return "Intermediate"
    return "Advanced"


def _score_shape(chord: Chord, frets: tuple[int, ...]) -> float:
    played = [f for f in frets if f != MUTED]
    if not played:
        return -999.0

    notes = _shape_notes(chord, frets)
    covered = _covered_note_names(chord, notes)
    root_pc = pitch_class(chord.root)
    bass_index = next((i for i, f in enumerate(frets) if f != MUTED), None)
    bass_pc = None if bass_index is None else _fret_note(STANDARD_TUNING[bass_index][1], frets[bass_index]) % 12

    score = 0.0
    score += len(set(pitch_class(n) for n in covered)) * 3.0
    if root_pc in {pitch_class(n) for n in covered}:
        score += 2.0
    if bass_pc == root_pc:
        score += 2.5
    elif bass_pc is not None:
        score += 0.4

    fretted = [f for f in frets if f > 0]
    if fretted:
        span = max(fretted) - min(fretted)
        score += max(0.0, 3.5 - span) * 1.25
        score -= max(fretted) * 0.10
    score += sum(1 for f in frets if f == OPEN) * 0.45
    score -= sum(1 for f in frets if f == MUTED) * 0.35
    return score


def _valid_shape(chord: Chord, frets: tuple[int, ...]) -> bool:
    played = [f for f in frets if f != MUTED]
    if len(played) < 3:
        return False

    notes = _shape_notes(chord, frets)
    covered = _covered_note_names(chord, notes)
    covered_pcs = {pitch_class(n) for n in covered}
    chord_pcs = {pitch_class(n) for n in chord.notes}
    if pitch_class(chord.root) not in covered_pcs:
        return False

    # Prefer at least three distinct harmonic tones whenever the chord contains
    # three or more; for large extensions, six strings cannot cover everything.
    required = min(3, len(chord_pcs))
    if len(covered_pcs) < required:
        return False

    # Avoid huge stretches within one shape.
    fretted = [f for f in frets if f > 0]
    if fretted and max(fretted) - min(fretted) > 5:
        return False
    return True


@lru_cache(maxsize=512)
def _find_guitar_voicings_cached(
    chord_name: str,
    root: str,
    quality: str,
    intervals: tuple[int, ...],
    notes: tuple[str, ...],
    limit: int,
) -> tuple[GuitarVoicing, ...]:
    # Reconstruct a lightweight Chord for cached searches.
    chord = Chord(
        root=root,
        quality=quality,
        intervals=intervals,
        notes=notes,
        display_name=chord_name,
    )

    # Search manageable five-fret windows instead of the combinatorial full
    # fretboard.  This still covers open position through fret 12 and strongly
    # biases toward playable shapes.
    windows = range(0, MAX_FRET - 4 + 1)
    all_shapes: list[GuitarVoicing] = []

    for start_fret in windows:
        end_fret = min(MAX_FRET, start_fret + 4)
        candidates: list[list[int]] = []
        for string_index in range(6):
            options = [
                fret
                for fret in _candidate_frets(chord, string_index)
                if start_fret <= fret <= end_fret
                or (start_fret == 0 and fret == OPEN)
            ]
            # Always permit muting.
            candidates.append(options + [MUTED])

        for choices in product(*candidates):
            frets = tuple(choices)
            if not _valid_shape(chord, frets):
                continue
            notes_played = _shape_notes(chord, frets)
            covered = _covered_note_names(chord, notes_played)
            first = next((i for i, f in enumerate(frets) if f != MUTED), None)
            bass_note = None if first is None else notes_played[0]
            all_shapes.append(
                GuitarVoicing(
                    chord_name=chord.display_name,
                    frets=frets,
                    notes=notes_played,
                    covered_notes=covered,
                    bass_note=bass_note,
                    difficulty=_difficulty(frets),
                    score=round(_score_shape(chord, frets), 6),
                )
            )

    all_shapes.sort(
        key=lambda v: (
            v.score,
            -sum(1 for f in v.frets if f == MUTED),
            v.frets,
        ),
        reverse=True,
    )

    unique: list[GuitarVoicing] = []
    seen: set[tuple[int, ...]] = set()
    for voicing in all_shapes:
        if voicing.frets in seen:
            continue
        seen.add(voicing.frets)
        unique.append(voicing)
        if len(unique) == limit:
            break

    return tuple(unique)


def find_guitar_voicings(chord: Chord, limit: int = 5) -> list[GuitarVoicing]:
    """Find highly playable standard-tuning voicings up to fret 12."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    result = _find_guitar_voicings_cached(
        chord.display_name,
        chord.root,
        chord.quality,
        chord.intervals,
        chord.notes,
        limit,
    )
    if not result:
        raise ValueError(f"No playable guitar voicing found for {chord.display_name}")
    return list(result)


def find_best_guitar_voicing(chord: Chord) -> GuitarVoicing:
    return find_guitar_voicings(chord, limit=1)[0]


def find_progression_voicings(chords: tuple[Chord, ...] | list[Chord]) -> tuple[GuitarVoicing, ...]:
    """Return one best playable voicing per chord in progression order."""
    return tuple(find_best_guitar_voicing(chord) for chord in chords)
