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
- Profiles include chord-vocabulary and curated progression-family preferences
- Chords and progression templates are scored against the combined profile

### Progression generation
- User-selectable 2–8 chords per progression
- User-selectable 1–8 progressions per generation
- Output labels dynamically as MAIN + alternatives
- Major and minor progression templates
- Mood/style-aware template weighting
- Candidate-chord scoring and functional transition scoring
- Deterministic generation when a seed is supplied
- Optional user-facing fixed seed controls for reproducible generation
- Seed is displayed with generated results; Regenerate/refinement advances the fixed seed by one
- Alternatives are selected for meaningful harmonic diversity
- Falls back to diatonic triads when necessary
- Harmonic-function awareness for Tonic, Predominant, Dominant, and Color movement
- Optional starting and ending scale-degree constraints
- Low/Balanced/High tension preference
- Flexible/Prefer Tonic/Strong Cadence resolution preference
- Balanced/Smooth/Expressive voice-leading preference using pitch-class movement

### Difficulty
- Calculates difficulty from the generated harmonic result
- Separate from the user's generation Complexity setting

### Step 4: Useful filtering
- Require selected scale degrees to appear in every generated progression
- Exclude selected scale degrees from generated progressions
- Set a maximum measured harmonic difficulty for results
- Filter results to Triads, Sevenths, Extensions, and/or Color chord families
- Active filters are shown with the generated result metadata
- Impossible filter combinations fail gracefully with an actionable message instead of crashing the Streamlit page

### Step 5: Result refinement and UI integration
- Result cards expose refinement actions without changing the underlying generator API
- Make simpler lowers generation Complexity by one level
- Make more complex raises generation Complexity by one level
- New progression preserves the current generation parameters and generates a fresh result with a new seed
- New mood changes only the selected mood set while preserving key, style, chord characteristics, harmony controls, and filters
- Refinements synchronize their parameter changes back into the Streamlit sidebar so the UI remains consistent with the generated result
- Boundary actions are disabled when Complexity is already Beginner or Experimental
- Refinement behavior is deterministic when supplied a test seed and is covered by dedicated integration tests

### Playing recommendations
- Mood/style/complexity-aware technique recommendation
- Simple immediately playable strumming/fingerstyle pattern
- Deterministic pattern selection when seeded

### Guitar voicings
- Standard-tuning playable voicing search
- Chord-tone coverage, root/bass awareness, and voicing difficulty
- Voicings attached to generated progressions

### Final seed feature
- Optional fixed-seed mode in the Streamlit sidebar for reproducible results
- User-editable seed from 0 to 2,147,483,647
- One-click new seed generation
- Generate reuses a fixed seed; Regenerate and refinements advance it deterministically
- Automatic mode retains fresh random seeding for normal generation behavior

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

Current verified test status is tracked by the final test suite. Release verification, deployment hygiene, and the seed/reproducibility feature are covered by `RELEASE_CHECKLIST.md` and the automated tests.

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

### Step 6: Release finalization
- Release structure verifier for required files, source directories, caches, bytecode, and secrets
- Runtime and development dependencies separated for cleaner deployment
- GitHub Actions CI runs release verification, Python compilation, and the full pytest suite
- Deployment instructions verified against current Streamlit Community Cloud documentation
- Final release checklist included in `RELEASE_CHECKLIST.md`

### Current status
The application is release-ready from the repository/test/deployment configuration perspective. The final ZIP must still be extracted and tested as a package, and the deployed browser session should be smoke-tested after deployment.
