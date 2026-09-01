"""Small session-scoped i18n helper for Mody.

Only presentation text is translated. Internal values (database enums, states,
priorities, IDs and API payloads) stay unchanged.
"""

import streamlit as st

from i18n.translations import EN

SUPPORTED_LANGUAGES = ("pt", "en")
LANGUAGE_LABELS = {"pt": "Português", "en": "English"}
_SESSION_KEY = "language"


def get_language() -> str:
    language = st.session_state.get(_SESSION_KEY, "pt")
    return language if language in SUPPORTED_LANGUAGES else "pt"


def set_language(language: str) -> None:
    if language in SUPPORTED_LANGUAGES:
        st.session_state[_SESSION_KEY] = language


def t(text: str, **kwargs) -> str:
    """Translate a Portuguese source string for the current session.

    Portuguese is the source/fallback language, so missing English entries fail
    safely by showing the original Portuguese text rather than a broken key.
    """
    translated = EN.get(text, text) if get_language() == "en" else text
    return translated.format(**kwargs) if kwargs else translated


def translate_generated_text(text: str | None) -> str:
    """Translate service-generated user-facing text without changing services.

    Exact matches are preferred. A small phrase-level fallback handles adaptive
    messages that append a backlog sentence to an otherwise fixed message.
    """
    if text is None:
        return ""
    if get_language() != "en":
        return str(text)

    value = str(text)
    if value in EN:
        return EN[value]

    # Fixed service phrases may be concatenated (for example adaptive backlog
    # notes). Replacing known phrases preserves that deterministic behavior.
    for source in sorted(EN, key=len, reverse=True):
        if source in value:
            value = value.replace(source, EN[source])
    return value
