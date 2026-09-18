"""Pitch-class and note-spelling utilities."""

SHARP_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
NATURAL_PITCH = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def _accidental_offset(accidental: str) -> int:
    if accidental == '':
        return 0
    return sum(1 if char == '#' else -1 for char in accidental)


def parse_note(name: str) -> tuple[str, int]:
    """Return (letter, pitch_class) for a note using natural, single/double/triple sharp or flat spelling."""
    if not name:
        raise ValueError('Note cannot be empty')

    letter = name[0]
    if letter not in NATURAL_PITCH:
        raise ValueError(f'Unsupported note: {name}')

    accidental = name[1:]
    if accidental not in {'', '#', '##', '###', 'b', 'bb', 'bbb'}:
        raise ValueError(f'Unsupported accidental in note: {name}')

    pc = (NATURAL_PITCH[letter] + _accidental_offset(accidental)) % 12
    return letter, pc


def pitch_class(name: str) -> int:
    """Return the pitch class (0-11) for a note."""
    return parse_note(name)[1]


def note_name(pc: int, accidental: str = 'Sharp') -> str:
    """Return a simple chromatic note name from a pitch class."""
    if accidental not in {'Sharp', 'Flat'}:
        raise ValueError(f'Unsupported display accidental: {accidental}')
    return (SHARP_NAMES if accidental == 'Sharp' else FLAT_NAMES)[pc % 12]
