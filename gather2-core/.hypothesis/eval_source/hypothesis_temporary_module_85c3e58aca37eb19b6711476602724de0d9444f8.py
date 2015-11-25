from hypothesis.utils.conventions import not_set

def accept(f):
    def test_create_survey(self=not_set):
        return f(self)
    return test_create_survey
