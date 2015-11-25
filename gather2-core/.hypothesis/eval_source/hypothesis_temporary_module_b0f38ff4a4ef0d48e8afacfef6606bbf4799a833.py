from hypothesis.utils.conventions import not_set

def accept(f):
    def times(allow_naive=not_set, timezones=not_set):
        return f(allow_naive, timezones)
    return times
