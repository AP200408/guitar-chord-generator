import json
import re

from generator.playback import build_playback_html, progression_playback_data
from generator.progression import generate_progressions
from music.models import GeneratorParameters
from music.notes import pitch_class


def _parameters() -> GeneratorParameters:
    key = GeneratorParameters.build_key("C", "Normal", "Major")
    return GeneratorParameters(
        key=key,
        moods=("Dreamy",),
        styles=("Neo Soul",),
        complexity="Intermediate",
        characteristics=("Maj7", "9th"),
    )


def test_playback_data_matches_progression_chords():
    result = generate_progressions(_parameters(), seed=42).main
    data = progression_playback_data(result)

    assert [item.name for item in data.chords] == [
        chord.display_name for chord in result.chords
    ]
    assert [item.root_pitch_class for item in data.chords] == [
        pitch_class(chord.root)
        for chord in result.chords
    ]
    assert [item.intervals for item in data.chords] == [
        chord.intervals for chord in result.chords
    ]
    assert data.chord_duration_seconds > 0
    assert data.attack_seconds > 0
    assert data.release_seconds > 0


def test_playback_html_contains_valid_payload():
    progression = generate_progressions(_parameters(), seed=42).main
    html = build_playback_html(progression, element_id="main-play")

    assert 'id="main-play-button"' in html
    assert 'background:#ffffff' in html
    assert 'color:#111111' in html
    assert 'width:100%' in html
    assert 'min-width:0' in html
    assert 'white-space:nowrap' in html
    assert 'AudioContext' in html
    assert 'navigator.clipboard' not in html
    assert 'application/json' in html

    match = re.search(
        r'<script type="application/json" id="main-play-data">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None
    payload = json.loads(match.group(1))
    assert len(payload["chords"]) == 4
    assert all(chord["intervals"] for chord in payload["chords"])
    assert all(0 <= chord["root_pitch_class"] <= 11 for chord in payload["chords"])


def test_playback_html_rejects_invalid_element_id():
    progression = generate_progressions(_parameters(), seed=42).main

    for element_id in ("", "has space", "<script>", "a.b"):
        try:
            build_playback_html(progression, element_id=element_id)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid element id accepted: {element_id!r}")


def test_playback_html_escapes_json_script_terminator_characters():
    progression = generate_progressions(_parameters(), seed=42).main
    html = build_playback_html(progression, element_id="safe-id")

    match = re.search(
        r'<script type="application/json" id="safe-id-data">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None
    payload_source = match.group(1)
    assert "</script>" not in payload_source.lower()
    assert json.loads(payload_source)["chords"]
