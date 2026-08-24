from pathlib import Path

from backend.app.services.pdf_extractor import extract_text_from_pdf


TEST_PDF = Path(r"D:\RESUMECV_NEW.pdf")


def test_extract_text_from_pdf():
    text = extract_text_from_pdf(str(TEST_PDF))

    assert text is not None
    assert len(text) > 0
    assert "JENNIE MILEVA" in text
    assert "EDUCATION" in text
    assert "TECHNICAL SKILLS" in text