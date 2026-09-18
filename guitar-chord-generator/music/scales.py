"""Scale construction with correct diatonic spelling."""

from .notes import NATURAL_PITCH, parse_note

MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
NATURAL_MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)
HARMONIC_MINOR_STEPS = (0, 2, 3, 5, 7, 8, 11)
MELODIC_MINOR_STEPS = (0, 2, 3, 5, 7, 9, 11)  # ascending/jazz melodic minor

LETTER_ORDER = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

SCALE_STEPS = {
    'Major': MAJOR_STEPS,
    'Natural Minor': NATURAL_MINOR_STEPS,
    'Harmonic Minor': HARMONIC_MINOR_STEPS,
    'Melodic Minor': MELODIC_MINOR_STEPS,
}


def _parse_root(root: str) -> tuple[str, int]:
    """Return root letter and pitch class, supporting double accidentals."""
    letter, pc = parse_note(root)
    return letter, pc


def _offset_to_accidental(offset: int) -> str:
    if offset == 0:
        return ''
    if offset == 1:
        return '#'
    if offset == 2:
        return '##'
    if offset == -1:
        return 'b'
    if offset == -2:
        return 'bb'
    raise ValueError(f'Unsupported accidental offset: {offset}')


def _spelled_scale(root: str, steps: tuple[int, ...]) -> list[str]:
    root_letter, root_pc = _parse_root(root)
    start = LETTER_ORDER.index(root_letter)
    result: list[str] = []

    for degree, step in enumerate(steps):
        letter = LETTER_ORDER[(start + degree) % 7]
        target_pc = (root_pc + step) % 12
        natural_pc = NATURAL_PITCH[letter]

        raw_offset = (target_pc - natural_pc) % 12
        if raw_offset > 6:
            raw_offset -= 12

        accidental = _offset_to_accidental(raw_offset)
        result.append(letter + accidental)

    return result


def scale_notes(root: str, scale_type: str) -> list[str]:
    """Return correctly spelled notes for a supported scale type."""
    try:
        steps = SCALE_STEPS[scale_type]
    except KeyError as exc:
        raise ValueError(
            f'Unsupported scale type: {scale_type}. '
            f'Supported types: {", ".join(SCALE_STEPS)}'
        ) from exc

    return _spelled_scale(root, steps)
