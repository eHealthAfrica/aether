from hypothesis.utils.conventions import not_set

def accept(f):
    def test_create_survey_results(self, survey_response=not_set):
        return f(self, survey_response)
    return test_create_survey_results
