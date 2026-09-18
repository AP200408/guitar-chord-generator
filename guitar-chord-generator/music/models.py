from dataclasses import dataclass

VALID_ROOTS = ('A', 'B', 'C', 'D', 'E', 'F', 'G')
VALID_ACCIDENTALS = ('Normal', 'Sharp', 'Flat')
VALID_MODES = ('Major', 'Minor')
VALID_MINOR_SCALE_TYPES = ('Natural Minor', 'Harmonic Minor', 'Melodic Minor')


@dataclass(frozen=True)
class Key:
    root: str
    accidental: str
    mode: str
    minor_scale_type: str = 'Natural Minor'

    @property
    def root_name(self) -> str:
        return self.root + {'Normal': '', 'Sharp': '#', 'Flat': 'b'}[self.accidental]

    @property
    def scale_type(self) -> str:
        """Return the concrete scale represented by this key."""
        return 'Major' if self.mode == 'Major' else self.minor_scale_type

    @property
    def name(self) -> str:
        if self.mode == 'Major':
            return f'{self.root_name} Major'
        return f'{self.root_name} {self.minor_scale_type}'

    def __post_init__(self) -> None:
        if self.root not in VALID_ROOTS:
            raise ValueError(f'Unsupported root: {self.root}')
        if self.accidental not in VALID_ACCIDENTALS:
            raise ValueError(f'Unsupported accidental: {self.accidental}')
        if self.mode not in VALID_MODES:
            raise ValueError(f'Unsupported key mode: {self.mode}')
        if self.mode == 'Minor' and self.minor_scale_type not in VALID_MINOR_SCALE_TYPES:
            raise ValueError(
                f'Unsupported minor scale type: {self.minor_scale_type}. '
                f'Use one of {VALID_MINOR_SCALE_TYPES}'
            )
        if self.mode == 'Major' and self.minor_scale_type != 'Natural Minor':
            raise ValueError('Major keys must use the default Natural Minor placeholder')


@dataclass(frozen=True)
class Chord:
    root: str
    quality: str
    intervals: tuple[int, ...]
    notes: tuple[str, ...]
    display_name: str
    roman_numeral: str | None = None


@dataclass(frozen=True)
class GuitarVoicing:
    chord_name: str
    frets: tuple[int, int, int, int, int, int]
    notes: tuple[str, ...]
    covered_notes: tuple[str, ...]
    bass_note: str | None
    difficulty: str
    score: float

    @property
    def tab(self) -> str:
        return " ".join("X" if fret == -1 else str(fret) for fret in self.frets)


@dataclass(frozen=True)
class GeneratorParameters:
    key: Key
    moods: tuple[str, ...]
    styles: tuple[str, ...]
    complexity: str
    characteristics: tuple[str, ...]
    chords_per_progression: int = 4
    progression_count: int = 4
    start_degree: int | None = None
    end_degree: int | None = None
    tension_preference: str = 'Balanced'
    resolution_preference: str = 'Flexible'
    voice_leading_preference: str = 'Balanced'
    required_degrees: tuple[int, ...] = ()
    excluded_degrees: tuple[int, ...] = ()
    max_difficulty: str = 'Any'
    chord_families: tuple[str, ...] = ()

    @staticmethod
    def build_key(
        root: str,
        accidental: str,
        key_type: str,
        minor_scale_type: str = 'Natural Minor',
    ) -> Key:
        return Key(root, accidental, key_type, minor_scale_type)
