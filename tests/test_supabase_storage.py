import io

from app.storage.supabase import SupabaseStorage


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"", text: str = ""):
        self.status_code = status_code
        self.content = content
        self.text = text


class FakeClient:
    objects: dict[str, bytes] = {}

    def __init__(self, **kwargs):
        self.options = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, *, headers, content):
        key = url.rsplit("/", 1)[-1]
        self.objects[key] = content.read()
        return FakeResponse(200)

    def get(self, url, *, headers):
        key = url.rsplit("/", 1)[-1]
        if key not in self.objects:
            return FakeResponse(404)
        return FakeResponse(200, self.objects[key])

    def delete(self, url, *, headers):
        key = url.rsplit("/", 1)[-1]
        self.objects.pop(key, None)
        return FakeResponse(204)

    def head(self, url, *, headers):
        key = url.rsplit("/", 1)[-1]
        return FakeResponse(200 if key in self.objects else 404)


def test_supabase_storage_round_trip(monkeypatch):
    FakeClient.objects.clear()
    monkeypatch.setattr("app.storage.supabase.httpx.Client", FakeClient)
    storage = SupabaseStorage(
        url="https://example.supabase.co",
        key="service-role-test-key",
        bucket="unidocs",
    )

    assert storage.save("university/file.txt", io.BytesIO(b"UniDocs")) == "university/file.txt"
    assert storage.exists("university/file.txt") is True
    assert storage.open("university/file.txt").read() == b"UniDocs"
    storage.delete("university/file.txt")
    assert storage.exists("university/file.txt") is False
