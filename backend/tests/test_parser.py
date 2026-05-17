"""Parser unit tests."""
from app.rag.parser import detect_section_path, parse_bytes


def test_parse_txt_bytes():
    content = "Раздел I. Общие положения.\n\nСтатья 1. Предмет регулирования.\n\nЭтот закон..."
    parsed = parse_bytes(content.encode("utf-8"), "test.txt")
    assert "Раздел I" in parsed
    assert "Статья 1" in parsed


def test_parse_html_bytes_strips_scripts():
    html = "<html><head><script>alert(1)</script></head><body><p>Текст</p></body></html>".encode("utf-8")
    parsed = parse_bytes(html, "test.html")
    assert "Текст" in parsed
    assert "alert" not in parsed
    assert "script" not in parsed.lower()


def test_detect_section_path():
    snippet = "Раздел II. Гранты\n\nСтатья 5. Условия предоставления"
    path = detect_section_path(snippet)
    assert path is not None
    assert "Раздел II" in path
    assert "Статья 5" in path


def test_detect_section_path_returns_none_for_unstructured():
    snippet = "Просто текст без структуры. Никаких разделов и статей."
    assert detect_section_path(snippet) is None
