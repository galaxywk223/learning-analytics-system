from config import normalize_postgres_url


def test_normalize_postgres_url_repairs_non_utf8_percent_encoding():
    raw = "postgresql://demo:%D6%D0%CE%C4@localhost:5432/learning_analytics_system"
    normalized = normalize_postgres_url(raw)
    assert normalized is not None
    assert "%D6%D0%CE%C4" not in normalized
    assert "%E4%B8%AD%E6%96%87" in normalized


def test_normalize_postgres_url_strips_wrapping_quotes_and_whitespace():
    raw = '  "postgresql://demo:%D6%D0@localhost:5432/learning_analytics_system"  '
    normalized = normalize_postgres_url(raw)
    assert normalized is not None
    assert normalized.startswith("postgresql://")
    assert "%D6%D0" not in normalized
    assert "%E4%B8%AD" in normalized
