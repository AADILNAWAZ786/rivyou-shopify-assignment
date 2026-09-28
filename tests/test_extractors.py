from types import SimpleNamespace

from app.detection import detect_shopify, detect_india, extract_state
from app.extractors import extract_contacts, extract_socials


def page(html):
    return SimpleNamespace(url="https://example.in/", html=html, text="Example")


def page(html):

    return SimpleNamespace(
        url="https://example.in/",
        html=html,
        text="Example"
    )


def test_shopify_detection():

    html = """
    <script>
        window.Shopify = {};
        Shopify.theme = {};
    </script>

    <link href="https://cdn.shopify.com/test.css">
    """

    ok, score, signals = detect_shopify(
        html,
        "example.in"
    )

    assert ok is True

    assert score >= 4

    assert len(signals) > 0


def test_india_detection():

    text = (
        "Hyderabad, Telangana, India. "
        "Phone +91 9876543210"
    )

    state = extract_state(
        text
    )

    ok, score, evidence = detect_india(
        text,
        "example.in",
        state
    )

    assert state == "Telangana"

    assert ok is True

    assert "indian_phone" in evidence


def test_contacts_and_socials():

    html = """
    <a href="mailto:hello@example.in">
        Email
    </a>

    <a href="tel:+919876543210">
        Call
    </a>

    <a href="https://instagram.com/example">
        Instagram
    </a>
    """

    p = page(html)

    emails, phones = extract_contacts(
        [p]
    )

    socials = extract_socials(
        [p]
    )

    assert (
        "hello@example.in"
        in emails
    )

    assert any(
        "9876543210" in phone
        for phone in phones
    )

    assert (
        "instagram"
        in socials
    )