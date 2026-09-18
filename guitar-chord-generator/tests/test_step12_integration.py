from pathlib import Path

from generator.playback import build_playback_html
from generator.progression import generate_progressions
from music.models import GeneratorParameters


ROOT = Path(__file__).parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")


def _parameters() -> GeneratorParameters:
    key = GeneratorParameters.build_key("A", "Flat", "Major")
    return GeneratorParameters(
        key=key,
        moods=("Dreamy", "Soulful"),
        styles=("Neo Soul", "R&B"),
        complexity="Advanced",
        characteristics=("Maj7", "9th", "6/9"),
    )


def test_generated_progression_has_previewable_audio_payload():
    result = generate_progressions(_parameters(), seed=2026)
    assert len(result.all_progressions) == 4
    for index, progression in enumerate(result.all_progressions):
        html = build_playback_html(progression, element_id=f"step12-{index}")
        assert "AudioContext" in html
        assert all(chord.display_name in html for chord in progression.chords)


def test_app_uses_playback_renderer():
    assert "build_playback_html" in APP_SOURCE
    assert 'components.html(' in APP_SOURCE
    assert 'element_id=f"{label.lower().replace(\' \', \'-\')}-play"' in APP_SOURCE


def test_app_has_no_step_placeholder_generation_text():
    assert "placeholder" not in APP_SOURCE.lower()
    assert "Step 7:" not in APP_SOURCE
    assert "parameter selection will be connected" not in APP_SOURCE


def test_app_exposes_output_count_controls_and_centered_white_buttons():
    assert '"Chords per Progression"' in APP_SOURCE
    assert '"Number of Progressions"' in APP_SOURCE
    assert 'justify-content: center;' in APP_SOURCE
    assert 'background: #ffffff;' in APP_SOURCE
    assert 'color: #111111;' in APP_SOURCE


def test_requested_output_controls_are_visible_in_generator_parameters():
    params = _parameters()
    assert params.chords_per_progression == 4
    assert params.progression_count == 4


def test_play_and_copy_controls_use_simple_text_labels():
    assert '>Copy</button>' in APP_SOURCE
    assert 'aria-label="Copy progression"' in APP_SOURCE
    playback_source = (ROOT / "generator" / "playback.py").read_text(encoding="utf-8")
    assert 'button_label: str = "Play"' in playback_source
    assert '>{safe_label}</button>' in playback_source
    assert '>Play</button>' not in APP_SOURCE  # playback is rendered by the dedicated module
    assert 'st.button("♡", key=' in APP_SOURCE


def test_copy_feedback_uses_simple_text_labels():
    assert "button.textContent = 'Copied'" in APP_SOURCE
    assert "button.textContent = 'Failed'" in APP_SOURCE
    assert "button.textContent = 'Copy'" in APP_SOURCE
