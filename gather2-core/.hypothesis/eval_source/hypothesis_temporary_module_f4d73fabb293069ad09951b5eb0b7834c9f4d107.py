from hypothesis.utils.conventions import not_set

def accept(f):
    def lists(elements=not_set, min_size=not_set, average_size=not_set, max_size=not_set, unique_by=not_set, unique=not_set):
        return f(elements, min_size, average_size, max_size, unique_by, unique)
    return lists
