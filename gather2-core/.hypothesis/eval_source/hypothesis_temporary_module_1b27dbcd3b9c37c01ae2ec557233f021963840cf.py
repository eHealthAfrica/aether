from hypothesis.utils.conventions import not_set

def accept(f):
    def datetimes(allow_naive=not_set, timezones=not_set, min_year=not_set, max_year=not_set):
        return f(allow_naive, timezones, min_year, max_year)
    return datetimes
