_whitespace = ' '

_ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
_ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_ascii_letters = _ascii_lowercase + _ascii_uppercase

_digits = '0123456789'
_alphanumeric = _digits + _ascii_letters

_punctuation = "'!#$%&()+,-.;=@[]^_`{}~"

_allowed = _whitespace + _alphanumeric + _punctuation


def sanitize_filename(value):
    return ''.join([c if c in _allowed else '_' for c in value])
