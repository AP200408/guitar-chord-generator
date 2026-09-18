import pytest

from music.chord_candidates import (
    get_chord_candidates,
    get_chord_candidates_in_key,
)
from music.models import Key


def _names(chords):
    return [chord.display_name for chord in chords]


def test_major_seventh_is_contextual_on_major_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 1, ['Maj7'], 'Beginner')
    assert _names(chords) == ['Cmaj7']


def test_minor_seventh_is_contextual_on_minor_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 2, ['m7'], 'Beginner')
    assert _names(chords) == ['Dm7']


def test_generic_ninth_resolves_to_major_ninth_in_major_tonic():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 1, ['9th'], 'Beginner')
    assert _names(chords) == ['Cmaj9']


def test_generic_ninth_resolves_to_minor_ninth_on_minor_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 2, ['9th'], 'Beginner')
    assert _names(chords) == ['Dm9']


def test_generic_ninth_resolves_to_dominant_ninth_on_fifth_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 5, ['9th'], 'Beginner')
    assert _names(chords) == ['G9']


def test_generic_extension_is_diatonic_on_beginner_level():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(key, 1, ['11th', '13th'], 'Beginner')
    assert _names(chords) == ['Cmaj11', 'Cmaj13']


def test_minor_generic_extensions_are_contextual():
    key = Key(root='C', accidental='Normal', mode='Minor')
    chords = get_chord_candidates(key, 1, ['9th', '11th', '13th'], 'Beginner')
    assert _names(chords) == ['Cm9', 'Cm11']
    advanced = get_chord_candidates(key, 1, ['13th'], 'Advanced')
    assert _names(advanced) == ['Cm13']


def test_minor_six_and_six_nine_are_supported():
    key = Key(
        root='A',
        accidental='Normal',
        mode='Minor',
        minor_scale_type='Melodic Minor',
    )
    chords = get_chord_candidates(key, 1, ['6th', '6/9'], 'Beginner')
    assert _names(chords) == ['Am6', 'Am6/9']


def test_add9_is_contextual_for_minor_chord():
    key = Key(root='A', accidental='Normal', mode='Minor')
    chords = get_chord_candidates(key, 1, ['Add9'], 'Beginner')
    assert _names(chords) == ['Amadd9']


def test_dominant_is_restricted_at_beginner_level_to_dominant_degree():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert _names(get_chord_candidates(key, 5, ['Dominant'], 'Beginner')) == ['G7']
    assert _names(get_chord_candidates(key, 1, ['Dominant'], 'Beginner')) == []


def test_altered_is_advanced_on_fifth_degree_only():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert _names(get_chord_candidates(key, 5, ['Altered'], 'Advanced')) == ['G7alt']
    assert _names(get_chord_candidates(key, 1, ['Altered'], 'Advanced')) == []
    assert _names(get_chord_candidates(key, 1, ['Altered'], 'Experimental')) == ['C7alt']


def test_quartal_is_available_from_intermediate():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert _names(get_chord_candidates(key, 1, ['Quartal'], 'Beginner')) == []
    assert _names(get_chord_candidates(key, 1, ['Quartal'], 'Intermediate')) == ['Cquartal']


def test_augmented_and_diminished_triads_are_strict_at_beginner():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert _names(get_chord_candidates(key, 7, ['Diminished'], 'Beginner')) == ['Bdim']
    assert _names(get_chord_candidates(key, 1, ['Diminished'], 'Beginner')) == []
    assert _names(get_chord_candidates(key, 1, ['Augmented'], 'Beginner')) == []


def test_harmonic_minor_tonic_mmaj7_is_diatonic():
    key = Key(
        root='A',
        accidental='Normal',
        mode='Minor',
        minor_scale_type='Harmonic Minor',
    )
    assert _names(get_chord_candidates(key, 1, ['mMaj7'], 'Beginner')) == ['AmMaj7']


def test_candidate_grouping_returns_all_seven_degrees():
    key = Key(root='C', accidental='Normal', mode='Major')
    result = get_chord_candidates_in_key(key, ['Maj7', 'm7', '9th'], 'Beginner')
    assert list(result) == ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    assert _names(result['I']) == ['Cmaj7', 'Cmaj9']
    assert _names(result['ii']) == ['Dm7', 'Dm9']
    assert _names(result['V']) == ['G9']


def test_characteristic_order_is_preserved_and_duplicates_removed():
    key = Key(root='C', accidental='Normal', mode='Major')
    chords = get_chord_candidates(
        key,
        5,
        ['Dominant', '7th', '9th'],
        'Beginner',
    )
    assert _names(chords) == ['G7', 'G9']


def test_invalid_degree_rejected():
    key = Key(root='C', accidental='Normal', mode='Major')
    with pytest.raises(ValueError, match='between 1 and 7'):
        get_chord_candidates(key, 0, ['Major'])


def test_invalid_characteristic_rejected():
    key = Key(root='C', accidental='Normal', mode='Major')
    with pytest.raises(ValueError, match='Unsupported chord characteristic'):
        get_chord_candidates(key, 1, ['Maj99'])


def test_invalid_complexity_rejected():
    key = Key(root='C', accidental='Normal', mode='Major')
    with pytest.raises(ValueError, match='Unsupported complexity'):
        get_chord_candidates(key, 1, ['Maj7'], 'Easy')


def test_major_scale_leading_tone_supports_half_diminished_seventh():
    key = Key(root='C', accidental='Normal', mode='Major')
    assert _names(get_chord_candidates(key, 7, ['7th'], 'Beginner')) == ['Bm7b5']


def test_natural_minor_second_degree_supports_half_diminished_seventh():
    key = Key(root='A', accidental='Normal', mode='Minor')
    assert _names(get_chord_candidates(key, 2, ['7th'], 'Beginner')) == ['Bm7b5']


def test_harmonic_minor_third_degree_supports_augmented_major_seventh():
    key = Key(root='A', accidental='Normal', mode='Minor', minor_scale_type='Harmonic Minor')
    assert _names(get_chord_candidates(key, 3, ['7th'], 'Beginner')) == ['Cmaj7#5']


def test_harmonic_minor_leading_tone_supports_diminished_seventh():
    key = Key(root='A', accidental='Normal', mode='Minor', minor_scale_type='Harmonic Minor')
    assert _names(get_chord_candidates(key, 7, ['7th'], 'Beginner')) == ['G#dim7']


def test_melodic_minor_sixth_degree_supports_half_diminished_seventh():
    key = Key(root='C', accidental='Normal', mode='Minor', minor_scale_type='Melodic Minor')
    assert _names(get_chord_candidates(key, 6, ['7th'], 'Beginner')) == ['Am7b5']
