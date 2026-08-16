import pytest

from app.services.file_validation import validate_extension, validate_magic_bytes, validate_size


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("notes.txt", b"plain academic notes"),
        ("data.json", b'{"course":"systems"}'),
        ("table.csv", b"name,score\nstudent,100"),
        ("notes.md", b"# Academic notes"),
        ("document.docx", b"PK\x03\x04fake-office-container"),
        ("sheet.xlsx", b"PK\x03\x04fake-office-container"),
        ("slides.pptx", b"PK\x03\x04fake-office-container"),
        ("legacy.doc", b"\xd0\xcf\x11\xe0legacy-office-container"),
    ],
)
def test_supported_document_formats_pass_validation(filename, content):
    extension = filename.rsplit(".", 1)[-1]
    validate_extension(
        filename,
        ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "odt", "ods", "odp", "csv", "md", "html", "htm", "xml", "json"],
    )
    validate_size(len(content), 50)
    validate_magic_bytes(content[:16], extension)
