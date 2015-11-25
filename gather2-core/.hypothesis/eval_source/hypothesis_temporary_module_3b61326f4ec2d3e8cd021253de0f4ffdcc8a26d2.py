from hypothesis.utils.conventions import not_set

def accept(f):
    def dates(min_year=not_set, max_year=not_set):
        return f(min_year, max_year)
    return dates
