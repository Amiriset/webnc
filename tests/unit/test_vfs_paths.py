"""Tests for webnc.vfs.paths — safe_path() and relative_path()."""
from pathlib import Path

from webnc.vfs.paths import safe_path, relative_path, DRIVE_LETTERS


class TestSafePath:
    def test_empty_string_defaults_to_c_drive(self):
        assert safe_path("") == Path("C:\\")

    def test_whitespace_only_defaults_to_c_drive(self):
        assert safe_path("   ") == Path("C:\\")

    def test_single_drive_letter(self):
        assert safe_path("/D") == Path("D:\\")

    def test_drive_letter_lowercase_normalized(self):
        assert safe_path("/d") == Path("D:\\")

    def test_drive_with_path(self):
        result = safe_path("/C/Users/test")
        assert result == Path("C:\\Users\\test")

    def test_drive_with_nested_path(self):
        result = safe_path("/E/projects/web/src")
        assert result == Path("E:\\projects\\web\\src")

    def test_backslashes_converted(self):
        result = safe_path("/C\\Users\\foo")
        assert result == Path("C:\\Users\\foo")

    def test_no_leading_slash(self):
        result = safe_path("D/projects/test")
        assert result == Path("D:\\projects\\test")

    def test_trailing_slash_stripped(self):
        result = safe_path("/C/Users/")
        assert result == Path("C:\\Users")

    def test_single_drive_letter_all_variants(self):
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            result = safe_path(f"/{letter}")
            assert result == Path(f"{letter}:\\")

    def test_drive_letter_only_lowercase(self):
        for letter in "abcdefghijklmnopqrstuvwxyz":
            result = safe_path(f"/{letter}")
            assert result == Path(f"{letter.upper()}:\\")
            assert result == Path(f"{letter.upper()}:\\\\")

    def test_deeply_nested_path(self):
        result = safe_path("/C/a/b/c/d/e/f")
        assert result == Path("C:\\a\\b\\c\\d\\e\\f")

    def test_path_with_spaces(self):
        result = safe_path("/C/Program Files/Test")
        assert result == Path("C:\\Program Files\\Test")

    def test_default_drive_for_invalid(self):
        result = safe_path("123/not_a_drive")
        assert result == Path("C:\\123\\not_a_drive")


class TestRelativePath:
    def test_root_drive(self):
        assert relative_path(Path("C:\\")) == "/C/"

    def test_nested_path(self):
        assert relative_path(Path("C:\\Users\\test")) == "/C/Users/test"

    def test_deeply_nested(self):
        assert relative_path(Path("E:\\a\\b\\c")) == "/E/a/b/c"

    def test_different_drive(self):
        assert relative_path(Path("D:\\projects")) == "/D/projects"

    def test_single_folder(self):
        assert relative_path(Path("C:\\Windows")) == "/C/Windows"

    def test_roundtrip_safe_path_relative(self):
        original = "/C/Users/test/file.txt"
        restored = relative_path(safe_path(original))
        assert restored == original

    def test_roundtrip_all_drives(self):
        for letter in "CDEFG":
            path = f"/{letter}/some/path"
            assert relative_path(safe_path(path)) == path


class TestDriveLetters:
    def test_drive_letters_are_26(self):
        assert len(DRIVE_LETTERS) == 26

    def test_drive_letters_are_uppercase(self):
        for ch in DRIVE_LETTERS:
            assert ch.isupper()
