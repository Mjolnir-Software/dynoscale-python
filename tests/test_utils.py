import asyncio
import logging
import time
from contextlib import nullcontext as does_not_raise

import pytest
import responses

from dynoscale.utils import (
    get_str_from_headers,
    fake_request_start_ms,
    is_valid_url,
    get_int_from_headers,
    get_int_from_bytestring_headers,
    ensure_module,
)

logging.basicConfig(level=logging.DEBUG)


# ========================= TESTS =============================
def test_ensure_module_finds_imported_module():
    # noinspection PyUnresolvedReferences
    import random
    a_random = ensure_module("random")
    assert a_random is not None
    assert a_random.__name__ == "random"
    assert a_random.randint(1, 1) == 1


def test_ensure_module_finds_existing_module():
    a_tabnanny = ensure_module("tabnanny")
    # tabnanny is in standard library, but shouldn't be imported not imported
    # this is purely to test cover the else branch of ensure_module function
    assert a_tabnanny is not None
    assert a_tabnanny.__name__ == "tabnanny"
    assert a_tabnanny.verbose == 0


def test_ensure_module_doesnt_find_a_module():
    a_module = ensure_module("this_module_for_sure_does_not_exist")
    assert a_module is None


# noinspection HttpUrlsUsage
@pytest.mark.parametrize(
    "key, result, headers, expectation",
    [
        # valid
        ("key", None, [], does_not_raise()),
        ("x-http-response-start", 10, [('X-HTTP-RESPONSE-START', '10',)], does_not_raise()),
        ("x-http-response-start", 20, [('X-HTTP-RESPONSE-START', '20', '21',)], does_not_raise()),
        ("x-http-response-start", 30, [['X-HTTP-RESPONSE-START', '30']], does_not_raise()),
        ("x-http-response-start", 40, [('X-HTTP-RESPONSE-START', 40)], does_not_raise()),
        ("x-http-response-start", 50, {'X-HTTP-RESPONSE-START': '50'}, does_not_raise()),
        ("x-http-response-start", 60, {'X-HTTP-RESPONSE-START': 60}, does_not_raise()),
        ("x-http-response-start", 61, {'X-HTTP-RESPONSE-START': '61'}, does_not_raise()),
        ("x-http-response-start", 70, (('X-HTTP-RESPONSE-START', 70,),), does_not_raise()),
        ("x-http-response-start", 71, (('X-HTTP-RESPONSE-START', "71",),), does_not_raise()),
        ("x-http-response-start", 80, (['X-HTTP-RESPONSE-START', '80'],), does_not_raise()),
        ("x-http-response-start", 81, (['X-HTTP-RESPONSE-START', 81],), does_not_raise()),
        ("key", 1, [("key", "1")], does_not_raise()),
        ("KEY", 2, [("kEy", "2")], does_not_raise()),
        ("Key", 3, [("key", "3")], does_not_raise()),
        ("key", -1, [("KEY", "-1")], does_not_raise()),
        ("KEY", -2, [("KEY", "-2")], does_not_raise()),
        ("Key", -3, [("KEY", "-3")], does_not_raise()),
        ("Key", 1, [("key", "1"), ("KEY", "2")], does_not_raise()),
        ("key", None, [("key", None)], does_not_raise()),
        ("key", None, [("key", "2.0")], does_not_raise()),
        ("key", None, [("key", "-2.0")], does_not_raise()),
        ("key", None, [("key", "-2.0")], does_not_raise()),
    ],
)
def test_get_int_from_headers_as_dict(key, result, headers, expectation):
    with expectation:
        if result is None:
            assert get_int_from_headers(key=key, headers=headers) is None
        else:
            assert get_int_from_headers(key=key, headers=headers) == result


@pytest.mark.parametrize(
    "key, result, headers, expectation",
    [
        # valid
        ("key", None, [], does_not_raise()),
        ("x-http-response-start", 10, [(b'X-HTTP-RESPONSE-START', b'10',)], does_not_raise()),
        ("x-http-response-start", 20, [(b'X-HTTP-RESPONSE-START', b'20', b'21',)], does_not_raise()),
        ("X-http-response-start", 30, [[b'X-HTTP-RESPONSE-START', b'30']], does_not_raise()),
        ("x-HTTP-response-start", None, [(b'X-HTTP-RESPONSE-START', "40")], does_not_raise()),
        ("x-http-response-start", None, [(b'X-HTTP-RESPONSE-START', 40)], does_not_raise()),
        ("x-http-response-start", None, [(b'X-HTTP-RESPONSE-START', 41)], does_not_raise()),
    ],
)
def test_get_int_from_bytestring_headers(key, result, headers, expectation):
    with expectation:
        if result is None:
            assert get_int_from_bytestring_headers(key=key, headers=headers) is None
        else:
            assert get_int_from_bytestring_headers(key=key, headers=headers) == result


def test_get_str_from_headers_accepts_list():
    headers = [("key", "val",)]
    s = get_str_from_headers(headers=headers, key="non-existent")
    assert s is None
    s = get_str_from_headers(headers=headers, key="non-existent", default="def")
    assert s == "def"
    s = get_str_from_headers(headers=headers, key="key")
    assert s == "val"
    s = get_str_from_headers(headers=headers, key="KEY")
    assert s == "val"
    s = get_str_from_headers(headers=headers, key="Key")
    assert s == "val"


def test_get_str_from_headers_returns_first_valid_record():
    headers = [("key", "val1",), ("key", "val2",)]
    s = get_str_from_headers(headers=headers, key="key")
    assert s == "val1"
    s = get_str_from_headers(headers=headers, key="kEy")
    assert s == "val1"


def test_get_str_from_headers_skips_over_invalid_list_items():
    headers = [
        (None, 2, "a"),
        ("key", None, "b"),
        ("key_", "c",),
        ("key", 'this', 'whatever',),
        ("kEy", "that",)
    ]
    s = get_str_from_headers(headers=headers, key="key")
    assert s == "this"
    s = get_str_from_headers(headers=headers, key="kEy")
    assert s == "this"


def test_get_str_from_headers_skips_over_invalid_dict_items():
    headers = {
        "a": (None, 2, "a"),
        1: [None, "b"],
        None: "",
        "key": [None, "b"],
        "key_": "c",
        "kEy": "this",
        "keY": 'that',
    }
    s = get_str_from_headers(headers=headers, key="key")
    assert s == "this"
    s = get_str_from_headers(headers=headers, key="keY")
    assert s == "this"


def test_fake_request_time_ms():
    lo = -5
    up = 5
    randoms = [fake_request_start_ms(lo, up) for _ in range(10_000)]

    def check_range(r):
        assert lo < r < up

    map(check_range, randoms)
    pass


# noinspection HttpUrlsUsage
@pytest.mark.parametrize(
    "url, is_valid, expectation",
    [
        # valid
        ("http://api.io/https", True, does_not_raise()),
        ("http://api.io", True, does_not_raise()),
        ("http://api.io/https?param", True, does_not_raise()),
        ("http://api.io/https?param=value", True, does_not_raise()),
        ("http://api.io/https?param=value#anchor", True, does_not_raise()),
        ("https://api.io/https", True, does_not_raise()),
        ("https://api.io", True, does_not_raise()),
        ("https://api.io/https?param", True, does_not_raise()),
        ("https://api.io/https?param=value", True, does_not_raise()),
        ("https://api.io/https?param=value#anchor", True, does_not_raise()),
        ("https://subdomain.api.io/https", True, does_not_raise()),
        ("https://subdomain.api.io", True, does_not_raise()),
        ("https://subdomain.api.io/https?param", True, does_not_raise()),
        ("https://subdomain.api.io/https?param=value", True, does_not_raise()),
        ("https://subdomain.api.io/https?param=value#anchor", True, does_not_raise()),
        ("https://subdomain.api.io/dir1/dir2/https", True, does_not_raise()),
        ("https://subdomain.api.io/dir1/dir2", True, does_not_raise()),
        ("https://subdomain.api.io/dir1/dir2/https?param", True, does_not_raise()),
        ("https://subdomain.api.io/dir1/dir2/https?param=value", True, does_not_raise()),
        ("https://subdomain.api.io/dir1/dir2/https?param=value#anchor", True, does_not_raise()),

        # invalid
        (None, False, does_not_raise()),
        (True, False, does_not_raise()),
        (False, False, does_not_raise()),
        ([], False, does_not_raise()),
        ((), False, does_not_raise()),
        ({}, False, does_not_raise()),
        (object, False, does_not_raise()),
        (b"", False, does_not_raise()),
        ("", False, does_not_raise()),
        ("http:", False, does_not_raise()),
        ("http://", False, does_not_raise()),
        ("http://", False, does_not_raise()),
        ("http://", False, does_not_raise()),
        ("https ://api.io/https", False, does_not_raise()),
        ("https: //api.io/https", False, does_not_raise()),
        ("https:/ /api.io/https", False, does_not_raise()),
        ("https:// api.io/https", False, does_not_raise()),
        ("https:// api.io/https ", False, does_not_raise()),
        ("https://apiio/https ", False, does_not_raise()),
        ("https://api.io /https ", False, does_not_raise()),
        ("https://api.io/ https ", False, does_not_raise()),
    ],
)
def test_is_valid_url(url, is_valid, expectation):
    with expectation:
        assert is_valid_url(url) == is_valid


@pytest.mark.asyncio
@responses.activate
async def test_async():
    sleep_time = 0.1
    before = time.time()
    await asyncio.sleep(sleep_time)
    after = time.time()
    assert before < after
    assert before + sleep_time < after
