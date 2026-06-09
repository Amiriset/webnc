"""E2E integration tests — real WindowsFileService + real filesystem via tmp_path."""
import io

import pytest
from pathlib import Path
from webnc.vfs.paths import relative_path


def _to_url(p: Path) -> str:
    return relative_path(p)


@pytest.fixture
def sample_tree(tmp_path):
    """Create a sample directory tree for E2E tests."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "hello.txt").write_text("hello world", encoding="utf-8")
    (src / "data.csv").write_text("a,b,c\n1,2,3", encoding="utf-8")
    sub = src / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested content", encoding="utf-8")
    return src


class TestE2EList:
    def test_list_directory(self, e2e_client, sample_tree):
        url = _to_url(sample_tree)
        r = e2e_client.get(f"/api/list?path={url}")
        assert r.status_code == 200
        data = r.json()
        names = [item["name"] for item in data["items"]]
        assert "hello.txt" in names
        assert "data.csv" in names
        assert "sub" in names
        assert data["total_files"] == 2
        assert data["total_dirs"] == 1

    def test_list_nonexistent_returns_400(self, e2e_client, tmp_path):
        url = _to_url(tmp_path / "nonexistent")
        r = e2e_client.get(f"/api/list?path={url}")
        assert r.status_code == 400

    def test_list_sort_by_size(self, e2e_client, sample_tree):
        url = _to_url(sample_tree)
        r = e2e_client.get(f"/api/list?path={url}&sort_by=size&sort_dir=desc")
        assert r.status_code == 200
        items = r.json()["items"]
        sizes = [i["size"] for i in items if not i["is_dir"]]
        assert sizes == sorted(sizes, reverse=True)


class TestE2EView:
    def test_view_text_file(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "hello.txt")
        r = e2e_client.get(f"/api/view?path={url}")
        assert r.status_code == 200
        assert r.json()["content"] == "hello world"

    def test_view_nonexistent_returns_400(self, e2e_client, tmp_path):
        url = _to_url(tmp_path / "missing.txt")
        r = e2e_client.get(f"/api/view?path={url}")
        assert r.status_code == 400


class TestE2EEdit:
    def test_edit_file(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "hello.txt")
        r = e2e_client.post("/api/edit", json={
            "path": url, "content": "updated content"
        })
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert (sample_tree / "hello.txt").read_text(encoding="utf-8") == "updated content"

    def test_edit_creates_new_file(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "new.txt")
        r = e2e_client.post("/api/edit", json={
            "path": url, "content": "brand new"
        })
        assert r.status_code == 200
        assert (sample_tree / "new.txt").read_text(encoding="utf-8") == "brand new"


class TestE2EMkdir:
    def test_mkdir(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "brand_new_dir")
        r = e2e_client.post("/api/mkdir", json={"path": url})
        assert r.status_code == 200
        assert (sample_tree / "brand_new_dir").is_dir()


class TestE2ERename:
    def test_rename_file(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "hello.txt")
        r = e2e_client.post("/api/rename", json={
            "path": url, "new_name": "renamed.txt"
        })
        assert r.status_code == 200
        assert (sample_tree / "renamed.txt").exists()
        assert not (sample_tree / "hello.txt").exists()


class TestE2EDelete:
    def test_delete_file(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "data.csv")
        r = e2e_client.post("/api/delete", json={"path": url, "recursive": False})
        assert r.status_code == 200
        assert not (sample_tree / "data.csv").exists()

    def test_delete_directory_recursive(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "sub")
        r = e2e_client.post("/api/delete", json={"path": url, "recursive": True})
        assert r.status_code == 200
        assert not (sample_tree / "sub").exists()


class TestE2EFileInfo:
    def test_file_info(self, e2e_client, sample_tree):
        url = _to_url(sample_tree / "hello.txt")
        r = e2e_client.get(f"/api/info?path={url}")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "hello.txt"
        assert data["size"] > 0
        assert data["is_dir"] is False


class TestE2ETree:
    def test_tree(self, e2e_client, sample_tree):
        url = _to_url(sample_tree)
        r = e2e_client.get(f"/api/tree?path={url}")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "dirs" in data or "nodes" in data


class TestE2EUploadDownload:
    def test_upload_and_download(self, e2e_client, sample_tree):
        dest = _to_url(sample_tree)
        content = b"binary test data"
        r = e2e_client.post(
            f"/api/upload?dest_dir={dest}",
            files={"file": ("upload_test.bin", io.BytesIO(content), "application/octet-stream")},
        )
        assert r.status_code == 200
        assert (sample_tree / "upload_test.bin").exists()

        dl_url = _to_url(sample_tree / "upload_test.bin")
        r2 = e2e_client.get(f"/api/download?path={dl_url}")
        assert r2.status_code == 200
        assert r2.content == content
