from hypothesis.utils.conventions import not_set

def accept(f):
    def characters(whitelist_categories=not_set, blacklist_categories=not_set, blacklist_characters=not_set, min_codepoint=not_set, max_codepoint=not_set):
        return f(whitelist_categories, blacklist_categories, blacklist_characters, min_codepoint, max_codepoint)
    return characters
