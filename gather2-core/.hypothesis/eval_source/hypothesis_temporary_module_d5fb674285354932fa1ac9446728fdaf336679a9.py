from hypothesis.utils.conventions import not_set

def accept(f):
    def test_create_survey(self, data=not_set):
        return f(self, data)
    return test_create_survey
