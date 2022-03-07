import math
import random
import re
import sys
import time
from importlib.machinery import ModuleSpec
from importlib.util import find_spec, module_from_spec
from types import ModuleType
from typing import Optional, Union, List, Tuple

# @formatter:off
# noinspection SpellCheckingInspection
ul = "\u00a1-\uffff"  # Unicode letters range (must not be a raw string).

# IP patterns
ipv4_re = (
    r"(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)"
    r"(?:\.(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)){3}"
)
ipv6_re = r"\[[0-9a-f:.]+\]"  # (simple regex, validated later)

# Host patterns
hostname_re = r"[a-z" + ul + r"0-9](?:[a-z" + ul + r"0-9-]{0,61}[a-z" + ul + r"0-9])?"

# Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
domain_re = r"(?:\.(?!-)[a-z" + ul + r"0-9-]{1,63}(?<!-))*"
tld_re = (
    r"\."  # dot
    r"(?!-)"  # can't start with a dash
    r"(?:[a-z" + ul + "-]{2,63}"  # domain label
    r"|xn--[a-z0-9]{1,59})"  # or punycode label
    r"(?<!-)"  # can't end with a dash
    r"\.?"  # may have a trailing dot
)
host_re = "(" + hostname_re + domain_re + tld_re + "|localhost)"

url_re = (
    r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
    r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
    r"(?:" + ipv4_re + "|" + ipv6_re + "|" + host_re + ")"  # host
    r"(?::[0-9]{1,5})?"  # port
    r"(?:[/?#][^\s]*)?"  # resource path
    r"\Z"
)
# @formatter:on


def epoch_s() -> int:
    return math.floor(time.time_ns() / 1_000_000_000)


def epoch_ms() -> int:
    return math.floor(time.time_ns() / 1_000_000)


def ensure_module(name: str) -> Optional[ModuleType]:
    if name in sys.modules:
        return sys.modules.get(name, None)
    elif find_spec(name) is not None:
        spec: ModuleSpec = find_spec(name)
        module: ModuleType = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module


def get_int_from_headers(
        headers: Union[dict, List[Tuple[str, str]]],
        key: str, default: Optional[int] = None
) -> Optional[int]:
    result = default
    try:
        if isinstance(headers, dict):
            headers = headers.items()
        candidates = [i for i in headers if len(i) > 1
                      and isinstance(i[0], str)
                      and (isinstance(i[1], int) or isinstance(i[1], float) or isinstance(i[1], str))
                      ]
        values = [i[1] for i in candidates if i[0].lower() == key.lower()]
        value = values[0] if len(values) > 0 else default
        result = int(value)
    finally:
        return result


def get_str_from_headers(
        headers: Union[dict, List[Tuple[str, str]]],
        key: str, default: Optional[str] = None
) -> Optional[str]:
    if isinstance(headers, dict):
        headers = headers.items()
    candidates = [i for i in headers if len(i) > 1 and isinstance(i[0], str) and isinstance(i[1], str)]
    values = [i[1] for i in candidates if i[0].lower() == key.lower()]
    value = values[0] if len(values) > 0 else default
    return value if isinstance(value, str) else default


def pseudo_normal_random(lower: int = 0, upper: int = 100, quality: int = 10) -> int:
    """Generate a value between min-max in a normal distribution"""
    values = sum([random.randint(lower, upper) for _ in range(quality)])
    return math.floor(values / quality)


def fake_request_start_ms(lower: int = 0, upper: int = 2_000) -> int:
    # Generate random request start to something up to a second ago for local testing
    return epoch_ms() - pseudo_normal_random(lower, upper)


def is_valid_url(url: str):
    return isinstance(url, str) and bool(re.match(url_re, url, re.IGNORECASE))
