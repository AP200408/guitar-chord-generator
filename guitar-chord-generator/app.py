from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from generator.harmony_rules import chord_function, degree_choices
from generator.playback import build_playback_html
from generator.progression import GeneratedProgressions, Progression, generate_progressions
from generator.ui_state import randomized_parameters
from generator.filters import active_filter_labels
from generator.seeding import MAX_SEED, MIN_SEED, random_seed, seed_for_action
from generator.result_tools import (
    explain_functions,
    refinement_help,
    refinement_is_available,
    refinement_label,
    refine_parameters,
)
from music.key_chords import get_chords_in_key
from music.models import GeneratorParameters
from music.options import (
    ACCIDENTALS,
    CHORD_CHARACTERISTICS,
    COMPLEXITIES,
    CHORD_FAMILIES,
    DIFFICULTY_FILTERS,
    KEY_TYPES,
    MINOR_SCALE_TYPES,
    MOODS,
    MUSICAL_CHARACTERS,
    ROOT_NOTES,
    RESOLUTION_PREFERENCES,
    TENSION_LEVELS,
    VOICE_LEADING_PREFERENCES,
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
        "start_degree": None,
        "end_degree": None,
        "tension_preference": "Balanced",
        "resolution_preference": "Flexible",
        "voice_leading_preference": "Balanced",
        "required_degrees": [],
        "excluded_degrees": [],
        "max_difficulty": "Any",
        "chord_families": [],
        "last_result": None,
        "generation_seed": random_seed(),
        "use_fixed_seed": False,
        "saved_progressions": [],
        "pending_action": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _set_action(action: str) -> None:
    st.session_state.pending_action = action


def _set_new_seed() -> None:
    st.session_state.generation_seed = random_seed()


def _prepare_pending_seed() -> None:
    """Prepare a pending action's seed before any seed widget is instantiated."""
    action = st.session_state.pending_action
    if action is None or action.startswith("refine:"):
        return
    st.session_state.generation_seed = seed_for_action(
        st.session_state.generation_seed,
        action,
        st.session_state.use_fixed_seed,
    )


def _sync_session_to_parameters(parameters: GeneratorParameters) -> None:
    """Synchronize refinement changes back into the sidebar controls."""
    st.session_state.root = parameters.key.root
    st.session_state.accidental = parameters.key.accidental
    st.session_state.key_type = parameters.key.mode
    st.session_state.minor_scale_type = parameters.key.minor_scale_type
    st.session_state.moods = list(parameters.moods)
    st.session_state.styles = list(parameters.styles)
    st.session_state.complexity = parameters.complexity
    st.session_state.characteristics = list(parameters.characteristics)
    st.session_state.chords_per_progression = parameters.chords_per_progression
    st.session_state.progression_count = parameters.progression_count
    st.session_state.start_degree = parameters.start_degree
    st.session_state.end_degree = parameters.end_degree
    st.session_state.tension_preference = parameters.tension_preference
    st.session_state.resolution_preference = parameters.resolution_preference
    st.session_state.voice_leading_preference = parameters.voice_leading_preference
    st.session_state.required_degrees = list(parameters.required_degrees)
    st.session_state.excluded_degrees = list(parameters.excluded_degrees)
    st.session_state.max_difficulty = parameters.max_difficulty
    st.session_state.chord_families = list(parameters.chord_families)


def _apply_refinement(action: str) -> None:
    """Prepare a result refinement before Streamlit rebuilds the page."""
    record = st.session_state.get("last_result")
    if not record or record.get("parameters") is None:
        return

    parameters: GeneratorParameters = record["parameters"]
    refinement_seed = seed_for_action(
        st.session_state.generation_seed,
        "refine",
        st.session_state.use_fixed_seed,
    )
    refined = refine_parameters(parameters, action, seed=refinement_seed)
    st.session_state.generation_seed = refinement_seed
    _sync_session_to_parameters(refined)
    st.session_state.pending_action = f"refine:{action}"


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
    st.session_state.start_degree = randomized.start_degree
    st.session_state.end_degree = randomized.end_degree
    st.session_state.tension_preference = randomized.tension_preference
    st.session_state.resolution_preference = randomized.resolution_preference
    st.session_state.voice_leading_preference = randomized.voice_leading_preference
    st.session_state.required_degrees = list(randomized.required_degrees)
    st.session_state.excluded_degrees = list(randomized.excluded_degrees)
    st.session_state.max_difficulty = randomized.max_difficulty
    st.session_state.chord_families = list(randomized.chord_families)
    st.session_state.pending_action = "randomize"


def _degree_option_label(key, degree: int | None) -> str:
    if degree is None:
        return "Any"
    chord = get_chords_in_key(key)[degree - 1]
    function = chord_function(chord, key, degree)
    return f"{chord.roman_numeral} — {function}"


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
        if progression.functions:
            st.write(f"Harmonic function: {' → '.join(progression.functions)}")
        st.write(f"Difficulty: {progression.difficulty.display}")
        degree_text = " → ".join(map(str, progression.degrees))
        st.caption(f"Score: {progression.score:.2f} · Degrees: {degree_text}")
        with st.expander("Why these chords work"):
            for explanation in explain_functions(progression):
                st.write(f"• {explanation}")

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



_ensure_session_defaults()
_prepare_pending_seed()

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

    with st.expander("Seed / Reproducibility", expanded=False):
        st.checkbox(
            "Use fixed seed",
            key="use_fixed_seed",
            help=(
                "Keep the same seed for Generate so the same parameters reproduce "
                "the same progressions. Regenerate/refinement advances the seed by one."
            ),
        )
        if st.session_state.use_fixed_seed:
            st.number_input(
                "Seed",
                min_value=MIN_SEED,
                max_value=MAX_SEED,
                step=1,
                format="%d",
                key="generation_seed",
                help=f"Use any integer from {MIN_SEED} to {MAX_SEED}.",
            )
            st.button(
                "🎲 New seed",
                use_container_width=True,
                on_click=_set_new_seed,
            )
            st.caption("Generate again with the same settings and seed to reproduce a result.")
        else:
            st.caption("A fresh random seed is used for each generation action.")

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

    harmony_key = GeneratorParameters.build_key(root, accidental, key_type, minor_scale_type)
    with st.expander("Harmony Controls", expanded=False):
        start_degree = st.selectbox(
            "Starting Chord",
            degree_choices(),
            key="start_degree",
            format_func=lambda degree: _degree_option_label(harmony_key, degree),
            help="Any, or require the progression to begin on a specific scale degree.",
        )
        end_degree = st.selectbox(
            "Ending Chord",
            degree_choices(),
            key="end_degree",
            format_func=lambda degree: _degree_option_label(harmony_key, degree),
            help="Any, or require the progression to finish on a specific scale degree.",
        )
        tension_preference = st.selectbox(
            "Tension",
            TENSION_LEVELS,
            key="tension_preference",
            help="Guide the overall harmonic tension without overriding key or style.",
        )
        resolution_preference = st.selectbox(
            "Resolution",
            RESOLUTION_PREFERENCES,
            key="resolution_preference",
            help="Control how strongly the generator favors a resolving ending.",
        )
        voice_leading_preference = st.selectbox(
            "Voice Leading",
            VOICE_LEADING_PREFERENCES,
            key="voice_leading_preference",
            help="Prefer smoother note movement, a balance, or more contrast between chords.",
        )

    with st.expander("Filters", expanded=False):
        filter_degree_options = list(range(1, 8))
        required_degrees = st.multiselect(
            "Require scale degrees",
            filter_degree_options,
            key="required_degrees",
            format_func=lambda degree: _degree_option_label(harmony_key, degree),
            help="Every generated progression must contain each selected scale degree at least once.",
        )
        excluded_degrees = st.multiselect(
            "Exclude scale degrees",
            filter_degree_options,
            key="excluded_degrees",
            format_func=lambda degree: _degree_option_label(harmony_key, degree),
            help="Selected scale degrees cannot appear in generated progressions.",
        )
        max_difficulty = st.selectbox(
            "Maximum result difficulty",
            DIFFICULTY_FILTERS,
            key="max_difficulty",
            help="Reject results whose measured harmonic difficulty is above this level.",
        )
        chord_families = st.multiselect(
            "Allowed chord families",
            CHORD_FAMILIES,
            key="chord_families",
            help="Every chord in a result must belong to one of the selected families. Leave empty for any family.",
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
    start_degree=start_degree,
    end_degree=end_degree,
    tension_preference=tension_preference,
    resolution_preference=resolution_preference,
    voice_leading_preference=voice_leading_preference,
    required_degrees=tuple(required_degrees),
    excluded_degrees=tuple(excluded_degrees),
    max_difficulty=max_difficulty,
    chord_families=tuple(chord_families),
)

pending_action = st.session_state.pending_action
if pending_action is not None:
    st.session_state.pending_action = None

    # Fixed-seed Generate reproduces the same result; Regenerate and refinements
    # advance the seed so those actions still produce a fresh deterministic result.
    used_seed = st.session_state.generation_seed
    try:
        generated_result = generate_progressions(
            parameters,
            seed=used_seed,
        )
        generation_error = None
    except (RuntimeError, ValueError) as exc:
        generated_result = None
        generation_error = str(exc)
    st.session_state.last_result = {
        "action": pending_action,
        "parameters": parameters,
        "result": generated_result,
        "error": generation_error,
        "seed": used_seed,
        "seed_mode": "fixed" if st.session_state.use_fixed_seed else "automatic",
    }

left, right = st.columns([2.6, 1])

with left:
    st.subheader("Generated Progressions")

    if st.session_state.last_result is None:
        st.info("Choose your parameters and press Generate.")
    else:
        record = st.session_state.last_result
        active_parameters: GeneratorParameters = record["parameters"]
        result: GeneratedProgressions | None = record["result"]

        if result is None:
            st.error(record.get("error", "No progression could be generated with the selected settings."))
        else:
            filter_labels = active_filter_labels(active_parameters)
            seed_used = record.get("seed", st.session_state.generation_seed)
            seed_mode = record.get(
                "seed_mode",
                "fixed" if st.session_state.use_fixed_seed else "automatic",
            )
            st.caption(
                f"{active_parameters.key.name} · "
                f"Seed: {seed_used} ({seed_mode}) · "
                f"Mood: {', '.join(active_parameters.moods) or 'None'} · "
                f"Character: {', '.join(active_parameters.styles) or 'None'} · "
                f"Complexity: {active_parameters.complexity} · "
                f"{active_parameters.chords_per_progression} chords × "
                f"{active_parameters.progression_count} progressions · "
                f"Tension: {active_parameters.tension_preference} · "
                f"Resolution: {active_parameters.resolution_preference}"
            )
            if filter_labels:
                st.caption(" · ".join(filter_labels))

            st.markdown("**Refine this result**")
            refinement_columns = st.columns(4)
            refinement_actions = ("simpler", "complex", "new_progression", "new_mood")
            for column, action in zip(refinement_columns, refinement_actions):
                with column:
                    st.button(
                        refinement_label(action),
                        key=f"refine-{action}",
                        use_container_width=True,
                        disabled=not refinement_is_available(active_parameters, action),
                        help=refinement_help(action),
                        on_click=_apply_refinement,
                        args=(action,),
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
