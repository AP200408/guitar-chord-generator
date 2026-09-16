# Guitar Chord Generator

Python + Streamlit guitar chord/progression generator.

## Current implementation

### Music foundation
- Major, natural minor, harmonic minor, and melodic minor scales
- Key-aware diatonic chords
- Correct note spelling, including double/triple accidentals where required
- Canonical chord-quality definitions
- Context-aware chord candidates

### Harmony intelligence
- All product moods have explicit harmony profiles
- All musical-character styles have explicit harmony profiles
- Multiple moods/styles can be combined into one normalized profile
- Chords can be scored against the combined profile

### Progression generation
- User-selectable 2–8 chords per progression
- User-selectable 1–8 progressions per generation
- Output labels dynamically as MAIN + alternatives
- Major and minor progression templates
- Mood/style-aware template weighting
- Candidate-chord scoring and functional transition scoring
- Deterministic generation when a seed is supplied
- Alternatives are selected for meaningful harmonic diversity
- Falls back to diatonic triads when necessary

### Difficulty
- Calculates difficulty from the generated harmonic result
- Separate from the user's generation Complexity setting

### Playing recommendations
- Mood/style/complexity-aware technique recommendation
- Simple immediately playable strumming/fingerstyle pattern
- Deterministic pattern selection when seeded

### Guitar voicings
- Standard-tuning playable voicing search
- Chord-tone coverage, root/bass awareness, and voicing difficulty
- Voicings attached to generated progressions

### Step 11: Application integration
- Streamlit parameter controls for all generator inputs
- Generate, Regenerate, and Randomize are distinct
- Randomize changes parameters and immediately generates a result
- Regenerate preserves parameters and changes the generated result
- Generate/Regenerate use seeded quality-weighted sampling to avoid repeated results
- Main + dynamically numbered alternatives are displayed with difficulty, playing recommendation, patterns, and guitar voicings
- Buttons are centered and use a white visual treatment
- Small Copy controls are provided for each progression
- Saved progressions are kept in the current Streamlit session
- All Chords in Key updates from the selected key

## Test status

Current verified test status: 477 passing tests. Streamlit browser-runtime smoke testing requires launching the Streamlit process; the Python source, integration helpers, and test suite are verified in the build environment.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest -q
```

### Step 12: Finalization
- Browser-based progression audio preview using the Web Audio API
- Copy and Save controls retained and integrated with the final result cards
- Streamlit deployment configuration and generic process start command
- Final regression and integration tests

### Current status
The current verified test suite includes the full music foundation, generator, guitar, UI-state, playback, and Step 12 integration tests.
