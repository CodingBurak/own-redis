NULL_RESP = "$-1\r\n"
CRLF = "\r\n"

SIMPLE_STRING = '+'
ERROR = '-'
INTEGER = ':'
STRING = '$'
ARRAY = '*'
DICT = '%'


def split_by_CRLF(value: str):
    word, rest = value.split(CRLF, 1)
    return word, rest
