# -*- coding: utf-8 -*-
import random
import re
import string

REMOVE_WHITESPACE_PATTERN = re.compile(r'\s+')


def remove_whitespace(text):
    return re.sub(REMOVE_WHITESPACE_PATTERN, '', text).strip()


def get_regex_pattern(keywords):
    if not keywords:
        raise ValueError('keywords cannot empty')
    regex = f'{"|".join(keywords)}'
    return re.compile(regex, re.IGNORECASE)


def masking_for_email(email):

    def _masking_for_user_part(v):
        if not v:
            return v

        if len(v) <= 1:
            return v

        if len(v) <= 2:
            return f'{v[0]}{"*" * len(v[1:])}'

        return f'{v[0]}{"*" * len(v[1:-1])}{v[-1]}'

    def _masking_for_domain_part(v):
        if not v:
            return v

        if '.' not in v:
            return f'{v[0]}{"*" * len(v[1:])}'

        front, back = v.rsplit('.', 1)

        if len(front) <= 1:
            return f'{front}.{back}'

        return f'{front[0]}{"*" * len(front[1:])}.{back}'

    if not email or '@' not in email:
        return email

    user_part, domain_part = email.rsplit('@', 1)
    user_part = _masking_for_user_part(user_part)
    domain_part = _masking_for_domain_part(domain_part)
    return f'{user_part}@{domain_part}'


def get_random_tag(num):
    arr = string.ascii_letters + string.digits
    return ''.join([random.choice(arr) for _ in range(num)])
