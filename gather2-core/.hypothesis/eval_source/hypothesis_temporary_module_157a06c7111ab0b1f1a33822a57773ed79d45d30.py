from hypothesis.utils.conventions import not_set

def accept(f):
    def dictionaries(keys, values, dict_class=not_set, min_size=not_set, average_size=not_set, max_size=not_set):
        return f(keys, values, dict_class, min_size, average_size, max_size)
    return dictionaries
