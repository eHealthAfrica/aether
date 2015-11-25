from hypothesis.utils.conventions import not_set

def accept(f):
    def test_response_smoke_test(self, survey_response=not_set):
        return f(self, survey_response)
    return test_response_smoke_test
