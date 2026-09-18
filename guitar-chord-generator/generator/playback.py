"""Browser-side audio preview helpers for generated guitar progressions.

This module contains no Streamlit imports.  It converts a progression into a
small self-contained Web Audio API control that can be rendered by Streamlit.
The preview is intentionally simple and dependency-free; it is a harmonic
preview, not an attempt to synthesize a realistic guitar recording.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
import re

from music.notes import pitch_class

from .progression import Progression


@dataclass(frozen=True)
class PlaybackChord:
    """Compact JSON-safe description of one chord for Web Audio preview."""

    name: str
    root_pitch_class: int
    intervals: tuple[int, ...]


@dataclass(frozen=True)
class PlaybackData:
    """Playback payload for a progression."""

    chords: tuple[PlaybackChord, ...]
    chord_duration_seconds: float = 1.35
    attack_seconds: float = 0.035
    release_seconds: float = 0.20


def progression_playback_data(progression: Progression) -> PlaybackData:
    """Convert a generated progression into a browser-safe audio payload."""
    if not progression.chords:
        raise ValueError("progression must contain at least one chord")

    chords = tuple(
        PlaybackChord(
            name=chord.display_name,
            root_pitch_class=pitch_class(chord.root),
            intervals=tuple(int(interval) for interval in chord.intervals),
        )
        for chord in progression.chords
    )
    return PlaybackData(chords=chords)


def _payload_json(data: PlaybackData) -> str:
    payload = {
        "chords": [
            {"name": chord.name, "root_pitch_class": chord.root_pitch_class, "intervals": list(chord.intervals)}
            for chord in data.chords
        ],
        "chord_duration_seconds": data.chord_duration_seconds,
        "attack_seconds": data.attack_seconds,
        "release_seconds": data.release_seconds,
    }
    # Prevent a future user-controlled string from terminating the JSON script tag.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def build_playback_html(
    progression: Progression,
    *,
    element_id: str,
    button_label: str = "Play",
) -> str:
    """Build a self-contained Web Audio preview button."""
    if not element_id or not re.fullmatch(r"[A-Za-z0-9_-]+", element_id):
        raise ValueError("element_id must contain only letters, numbers, '_' or '-'")

    data = progression_playback_data(progression)
    safe_id = html.escape(element_id, quote=True)
    safe_label = html.escape(button_label, quote=True)
    data_json = _payload_json(data)

    return f"""
<style>html, body {{ margin:0; padding:0; width:100%; overflow:hidden; }}</style>
<div id="{safe_id}-wrap" style="width:100%;box-sizing:border-box;">
  <button id="{safe_id}-button" type="button" style="
    display:inline-flex;align-items:center;justify-content:center;
    width:100%;min-width:0;height:36px;box-sizing:border-box;
    border:1px solid #c8c8c8;border-radius:7px;
    background:#ffffff;color:#111111;
    padding:0 8px;cursor:pointer;font-size:16px;font-weight:600;
    line-height:1;white-space:nowrap;box-shadow:0 1px 2px rgba(0,0,0,.08);
  " aria-label="Play progression" title="Play progression">{safe_label}</button>
  <span id="{safe_id}-status" style="margin-left:7px;font-size:12px;opacity:.75;"></span>
</div>
<script type="application/json" id="{safe_id}-data">{data_json}</script>
<script>
(() => {{
  const button = document.getElementById("{safe_id}-button");
  const status = document.getElementById("{safe_id}-status");
  const payloadElement = document.getElementById("{safe_id}-data");
  if (!button || !payloadElement) return;

  const payload = JSON.parse(payloadElement.textContent);
  let audioContext = null;
  let stopTimer = null;

  const frequencyFor = (rootPitchClass, semitoneOffset) => {{
    const midi = 48 + rootPitchClass + semitoneOffset; // Root centered around C3.
    return 440 * Math.pow(2, (midi - 69) / 12);
  }};

  const playNote = (context, frequency, start, duration) => {{
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "triangle";
    oscillator.frequency.setValueAtTime(frequency, start);

    const attack = payload.attack_seconds;
    const release = payload.release_seconds;
    const peak = 0.075;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(peak, start + attack);
    gain.gain.setValueAtTime(peak, start + Math.max(attack, duration - release));
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);

    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(start);
    oscillator.stop(start + duration + 0.01);
  }};

  button.addEventListener("mouseenter", () => {{
    button.style.background = "#f4f4f4";
    button.style.borderColor = "#aaaaaa";
  }});
  button.addEventListener("mouseleave", () => {{
    button.style.background = "#ffffff";
    button.style.borderColor = "#c8c8c8";
  }});

  button.addEventListener("click", async () => {{
    try {{
      audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
      if (audioContext.state === "suspended") await audioContext.resume();

      const duration = payload.chord_duration_seconds;
      const now = audioContext.currentTime + 0.03;

      payload.chords.forEach((chord, chordIndex) => {{
        const chordStart = now + chordIndex * duration;
        chord.intervals.forEach((interval) => {{
          playNote(audioContext, frequencyFor(chord.root_pitch_class, interval), chordStart, duration * 0.92);
        }});
      }});

      const totalSeconds = payload.chords.length * duration;
      status.textContent = "♪";
      clearTimeout(stopTimer);
      stopTimer = setTimeout(() => {{ status.textContent = ""; }}, totalSeconds * 1000);
    }} catch (error) {{
      status.textContent = "Failed";
    }}
  }});
}})();
</script>
"""
