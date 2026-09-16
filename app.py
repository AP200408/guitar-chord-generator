from __future__ import annotations

import random

import streamlit as st
import streamlit.components.v1 as components

from generator.playback import build_playback_html
from generator.progression import GeneratedProgressions, Progression, generate_progressions
from generator.ui_state import randomized_parameters
from music.key_chords import get_chords_in_key
from music.models import GeneratorParameters
from music.options import (
    ACCIDENTALS,
    CHORD_CHARACTERISTICS,
    COMPLEXITIES,
    KEY_TYPES,
    MINOR_SCALE_TYPES,
    MOODS,
    MUSICAL_CHARACTERS,
    ROOT_NOTES,
)

st.set_page_config(
    page_title="Guitar Chord Generator",
    page_icon="🎸",
    layout="wide",
)

st.markdown("""
<style>
div.stButton > button {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: #ffffff;
    color: #111111;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    font-weight: 600;
}
div.stButton > button:hover {
    background: #f2f2f2;
    color: #111111;
    border-color: #aaaaaa;
}
</style>
""", unsafe_allow_html=True)


def _ensure_session_defaults() -> None:
    defaults = {
        "root": "C",
        "accidental": "Normal",
        "key_type": "Major",
        "minor_scale_type": "Natural Minor",
        "moods": ["Dreamy"],
        "styles": ["Neo Soul"],
        "complexity": "Intermediate",
        "characteristics": ["Maj7", "9th"],
        "chords_per_progression": 4,
        "progression_count": 4,
        "last_result": None,
        "generation_seed": random.randrange(1_000_000_000),
        "saved_progressions": [],
        "pending_action": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _set_action(action: str) -> None:
    st.session_state.pending_action = action


def _apply_randomization() -> None:
    randomized = randomized_parameters()
    st.session_state.root = randomized.root
    st.session_state.accidental = randomized.accidental
    st.session_state.key_type = randomized.key_type
    st.session_state.minor_scale_type = randomized.minor_scale_type
    st.session_state.moods = list(randomized.moods)
    st.session_state.styles = list(randomized.styles)
    st.session_state.complexity = randomized.complexity
    st.session_state.characteristics = list(randomized.characteristics)
    st.session_state.chords_per_progression = randomized.chords_per_progression
    st.session_state.progression_count = randomized.progression_count
    st.session_state.pending_action = "randomize"


def _copy_button(text: str, key: str) -> None:
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("</", "<\\/")
        .replace("\n", "\\n")
    )
    html = f"""
    <style>html, body {{ margin:0; padding:0; width:100%; overflow:hidden; }}</style>
    <div style="width:100%; box-sizing:border-box;">
    <button id="copy-{key}" type="button" style="
        display:inline-flex; align-items:center; justify-content:center;
        width:100%; min-width:0; height:36px; box-sizing:border-box;
        border:1px solid #c8c8c8; border-radius:7px;
        background:#ffffff; color:#111111;
        padding:0 8px; cursor:pointer; font-size:16px; font-weight:600;
        white-space:nowrap;
        line-height:1; box-shadow:0 1px 2px rgba(0,0,0,.08);
    " aria-label="Copy progression" title="Copy progression">Copy</button>
    <script>
    const button = document.getElementById('copy-{key}');
    button.addEventListener('mouseenter', () => {{
        button.style.background = '#f4f4f4';
        button.style.borderColor = '#aaaaaa';
    }});
    button.addEventListener('mouseleave', () => {{
        button.style.background = '#ffffff';
        button.style.borderColor = '#c8c8c8';
    }});

    button.addEventListener('click', async () => {{
        try {{
            await navigator.clipboard.writeText(`{safe_text}`);
            button.textContent = 'Copied';
            setTimeout(() => button.textContent = 'Copy', 1200);
        }} catch (error) {{
            button.textContent = 'Failed';
            setTimeout(() => button.textContent = 'Copy', 1200);
        }}
    }});
    </script>
    </div>
    """
    components.html(html, height=40, scrolling=False)


def _save_progression(progression: Progression) -> None:
    signature = progression.display_name
    if any(item.display_name == signature for item in st.session_state.saved_progressions):
        return
    st.session_state.saved_progressions.append(progression)
    st.toast("Progression saved")


def _render_progression(label: str, progression: Progression) -> None:
    with st.container(border=True):
        header_col, play_col, copy_col, save_col = st.columns([7, 1.3, 1.2, 1.2])
        with header_col:
            st.markdown(f"**{label}**")
        with play_col:
            components.html(
                build_playback_html(
                    progression,
                    element_id=f"{label.lower().replace(' ', '-')}-play",
                ),
                height=40,
            )
        with copy_col:
            _copy_button(progression.display_name, f"{label.lower().replace(' ', '-')}-copy")
        with save_col:
            if st.button("♡", key=f"save-{label}", use_container_width=True, help="Save progression"):
                _save_progression(progression)

        st.markdown(f"### {progression.display_name}")
        st.write(f"Roman numerals: {' → '.join(progression.roman_numerals)}")
        st.write(f"Difficulty: {progression.difficulty.display}")

        st.markdown("**Recommended playing**")
        st.write(progression.playing.technique)
        st.caption(progression.playing.pattern)
        st.caption(progression.playing.reason)

        if progression.voicings:
            st.markdown("**Guitar voicings (low E → high E)**")
            voicing_columns = st.columns(len(progression.chords))
            for column, chord, voicing in zip(voicing_columns, progression.chords, progression.voicings):
                with column:
                    st.caption(chord.display_name)
                    st.code(voicing.tab, language="text")
                    st.caption(f"{voicing.difficulty} · bass: {voicing.bass_note or '—'}")

        st.caption(f"Generator score: {progression.score:.2f}")


_ensure_session_defaults()

st.title("🎸 Guitar Chord Generator")
st.caption("Turn a mood and musical character into playable guitar chord progressions.")

with st.sidebar:
    st.header("Parameters")
    st.button(
        "🎲 Randomize",
        use_container_width=True,
        on_click=_apply_randomization,
        type="secondary",
    )
    st.caption("Randomize changes the parameters and generates a new result.")

    root = st.selectbox("Root", ROOT_NOTES, key="root")
    accidental = st.selectbox("Accidental", ACCIDENTALS, key="accidental")
    key_type = st.radio("Key Type", KEY_TYPES, horizontal=True, key="key_type")

    minor_scale_type = "Natural Minor"
    if key_type == "Minor":
        minor_scale_type = st.selectbox(
            "Minor Scale Type",
            MINOR_SCALE_TYPES,
            key="minor_scale_type",
        )
    else:
        st.session_state.minor_scale_type = "Natural Minor"

    moods = st.multiselect("Mood", MOODS, key="moods")
    styles = st.multiselect("Musical Character", MUSICAL_CHARACTERS, key="styles")
    complexity = st.selectbox("Complexity", COMPLEXITIES, key="complexity")
    characteristics = st.multiselect(
        "Chord Characteristics",
        CHORD_CHARACTERISTICS,
        key="characteristics",
    )
    chords_per_progression = st.selectbox(
        "Chords per Progression",
        list(range(2, 9)),
        key="chords_per_progression",
        help="How many chords should each generated progression contain.",
    )
    progression_count = st.selectbox(
        "Number of Progressions",
        list(range(1, 9)),
        key="progression_count",
        help="How many different progressions to generate.",
    )

    st.divider()
    generate_col, regenerate_col = st.columns(2)
    with generate_col:
        st.button(
            "Generate",
            use_container_width=True,
            type="primary",
            on_click=_set_action,
            args=("generate",),
        )
    with regenerate_col:
        st.button(
            "Regenerate",
            use_container_width=True,
            on_click=_set_action,
            args=("regenerate",),
        )

key = GeneratorParameters.build_key(root, accidental, key_type, minor_scale_type)
parameters = GeneratorParameters(
    key=key,
    moods=tuple(moods),
    styles=tuple(styles),
    complexity=complexity,
    characteristics=tuple(characteristics),
    chords_per_progression=chords_per_progression,
    progression_count=progression_count,
)

pending_action = st.session_state.pending_action
if pending_action is not None:
    st.session_state.pending_action = None

    # Randomize, Generate, and Regenerate all end in a new generated result.
    # They differ only in whether parameters change and whether the seed changes.
    st.session_state.generation_seed = random.randrange(1_000_000_000)
    st.session_state.last_result = {
        "action": pending_action,
        "parameters": parameters,
        "result": generate_progressions(
            parameters,
            seed=st.session_state.generation_seed,
        ),
    }

left, right = st.columns([2.6, 1])

with left:
    st.subheader("Generated Progressions")

    if st.session_state.last_result is None:
        st.info("Choose your parameters and press Generate.")
    else:
        record = st.session_state.last_result
        result: GeneratedProgressions = record["result"]
        active_parameters: GeneratorParameters = record["parameters"]

        st.caption(
            f"{active_parameters.key.name} · "
            f"Mood: {', '.join(active_parameters.moods) or 'None'} · "
            f"Character: {', '.join(active_parameters.styles) or 'None'} · "
            f"Complexity: {active_parameters.complexity} · "
            f"{active_parameters.chords_per_progression} chords × "
            f"{active_parameters.progression_count} progressions"
        )

        labels = ["MAIN"] + [f"ALTERNATIVE {i}" for i in range(1, len(result.all_progressions))]
        for label, progression in zip(labels, result.all_progressions):
            _render_progression(label, progression)

with right:
    st.subheader("All Chords in Key")
    st.caption(key.name)
    for chord in get_chords_in_key(key):
        st.write(f"**{chord.roman_numeral}** — {chord.display_name}")

    st.divider()
    st.subheader("Saved")
    if not st.session_state.saved_progressions:
        st.caption("No saved progressions yet.")
    else:
        for index, progression in enumerate(st.session_state.saved_progressions, start=1):
            st.write(f"**{index}.** {progression.display_name}")
