import random
import string


def rand_string_runes(n):
    letter_runes = string.ascii_letters
    return ''.join(random.choice(letter_runes) for _ in range(n))
