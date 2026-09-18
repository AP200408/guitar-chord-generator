from pathlib import Path

from generator.progression import generate_progressions
from generator.ui_state import randomized_parameters
from music.models import GeneratorParameters


ROOT = Path(__file__).parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def _to_generator_parameters(randomized):
    key = GeneratorParameters.build_key(
        randomized.root,
        randomized.accidental,
        randomized.key_type,
        randomized.minor_scale_type,
    )
    return GeneratorParameters(
        key=key,
        moods=randomized.moods,
        styles=randomized.styles,
        complexity=randomized.complexity,
        characteristics=randomized.characteristics,
        chords_per_progression=randomized.chords_per_progression,
        progression_count=randomized.progression_count,
    )


def test_randomized_parameters_generate_valid_product_output():
    for seed in range(25):
        randomized = randomized_parameters(seed)
        parameters = _to_generator_parameters(randomized)
        result = generate_progressions(parameters, seed=seed)

        assert len(result.all_progressions) == randomized.progression_count
        assert all(
            len(progression.chords) == randomized.chords_per_progression
            for progression in result.all_progressions
        )
        assert all(progression.difficulty.level for progression in result.all_progressions)
        assert all(progression.playing.technique for progression in result.all_progressions)
        assert all(progression.voicings for progression in result.all_progressions)


def test_application_is_using_real_step11_features():
    required_snippets = (
        "randomized_parameters",
        "get_chords_in_key",
        '"Generate",',
        '"Regenerate",',
        '"🎲 Randomize",',
        '>Copy</button>',
        'st.button("♡",',
        'progression.difficulty.display',
        'progression.playing.technique',
        'progression.voicings',
    )
    for snippet in required_snippets:
        assert snippet in APP_SOURCE


def test_old_placeholder_randomize_message_is_removed():
    assert "parameter selection will be connected" not in APP_SOURCE
    assert "Step 7:" not in APP_SOURCE
