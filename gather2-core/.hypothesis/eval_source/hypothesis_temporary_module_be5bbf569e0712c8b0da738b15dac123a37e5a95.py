from hypothesis.utils.conventions import not_set

def accept(f):
    def test_survey_smoke_test(self, data=not_set):
        return f(self, data)
    return test_survey_smoke_test
