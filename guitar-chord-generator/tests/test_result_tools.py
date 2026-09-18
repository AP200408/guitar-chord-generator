from generator.result_tools import explain_functions, progression_summary, refine_parameters
from generator.progression import generate_progressions
from music.models import GeneratorParameters


def params(complexity="Intermediate"):
    return GeneratorParameters(
        key=GeneratorParameters.build_key("C", "Normal", "Major"),
        moods=("Dreamy",), styles=("Neo Soul",), complexity=complexity,
        characteristics=("Maj7", "9th"), chords_per_progression=4,
        progression_count=4,
    )


def test_summary_and_function_explanations_match_progression():
    progression = generate_progressions(params(), seed=11).main
    summary = progression_summary(progression)
    assert summary["chords"] == tuple(c.display_name for c in progression.chords)
    assert len(explain_functions(progression)) == len(progression.chords)


def test_refinement_changes_only_complexity_for_simple_actions():
    original = params("Intermediate")
    assert refine_parameters(original, "simpler").complexity == "Beginner"
    assert refine_parameters(original, "complex").complexity == "Advanced"
    assert refine_parameters(original, "simpler").key == original.key
    assert refine_parameters(original, "complex").moods == original.moods


def test_refinement_rejects_unknown_action():
    try:
        refine_parameters(params(), "invalid")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid refinement action was accepted")
