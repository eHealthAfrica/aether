from hypothesis.utils.conventions import not_set

def accept(f):
    def sets(elements=not_set, min_size=not_set, average_size=not_set, max_size=not_set):
        return f(elements, min_size, average_size, max_size)
    return sets
