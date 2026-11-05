"""Shared choices for optional LGBTQIA+ self-identification."""

LGBTQIA_CATEGORIES = (
    ("lesbian", "Lesbian"),
    ("gay", "Gay"),
    ("bisexual", "Bisexual"),
    ("pansexual", "Pansexual"),
    ("transgender", "Transgender"),
    ("non_binary", "Non-binary"),
    ("queer", "Queer"),
    ("questioning", "Questioning"),
    ("intersex", "Intersex"),
    ("asexual", "Asexual"),
    ("another_identity", "Another LGBTQIA+ identity"),
)
LGBTQIA_CATEGORY_VALUES = {value for value, _label in LGBTQIA_CATEGORIES}
