from __future__ import annotations

import codecs
import hashlib
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from solidlsp.ls_exceptions import SolidLSPException
from solidlsp.ls_utils import FileUtils, PlatformId, PlatformUtils


class _FakeResponse:
    def __init__(self, payload: bytes, final_url: str) -> None:
        self.status_code = 200
        self.headers = {"content-encoding": "gzip"}
        self.url = final_url
        self._payload = payload

    def iter_content(self, chunk_size: int = 1):
        for offset in range(0, len(self._payload), chunk_size):
            yield self._payload[offset : offset + chunk_size]

    def close(self) -> None:
        return None


def test_download_file_verified_writes_decoded_response_body(tmp_path: Path) -> None:
    """Gzip-encoded transfer bodies should be written as decoded payload bytes."""
    payload = b"PK\x03\x04zip-content"
    target_path = tmp_path / "downloaded.vsix"
    final_url = "https://marketplace.visualstudio.com/example.vsix"

    with patch(
        "solidlsp.ls_utils.requests.get",
        return_value=_FakeResponse(payload, final_url),
    ):
        FileUtils.download_file_verified(
            "https://marketplace.visualstudio.com/example.vsix",
            str(target_path),
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            allowed_hosts=("marketplace.visualstudio.com",),
        )

    assert target_path.read_bytes() == payload


# A file that cannot be decoded with the project encoding, forcing read_file's
# charset_normalizer fallback. The accented characters make the bytes invalid UTF-8,
# and the content is long enough for encoding detection to be reliable.
_CP1252_LINES = [
    "# -*- coding: cp1252 -*-",
    "# Author: José Fernández",
    "# Copyright (c) 2019 Müller & Söhne GmbH.",
    "",
    "import os",
    "",
    "",
    "class ConfiguracionBasica:",
    '    """Clase de configuración para el módulo de facturación."""',
    "",
    "    def __init__(self, nombre, valor=None):",
    "        self.nombre = nombre",
    "        self.valor = valor",
    "",
    "    def describir(self):",
    '        return f"{self.nombre}: {self.valor}"',
]


def test_read_file_fallback_normalizes_crlf(tmp_path: Path) -> None:
    """The charset_normalizer fallback should apply universal newlines, just like the primary path."""
    file_path = tmp_path / "config_cp1252.py"
    file_path.write_bytes(("\r\n".join(_CP1252_LINES) + "\r\n").encode("cp1252"))

    # guard against a vacuous test: the fixture must actually force the fallback
    with pytest.raises(UnicodeDecodeError):
        file_path.read_text(encoding="utf-8")

    content = FileUtils.read_file(str(file_path), "utf-8")

    assert "José Fernández" in content, "fallback should decode the file as cp1252"
    assert "\r" not in content
    assert content.splitlines() == _CP1252_LINES


def test_read_file_fallback_normalizes_lone_cr(tmp_path: Path) -> None:
    """Old-style lone CR separators should be normalized by the fallback as well."""
    file_path = tmp_path / "lone_cr_cp1252.py"
    file_path.write_bytes(("\r".join(_CP1252_LINES) + "\r").encode("cp1252"))

    content = FileUtils.read_file(str(file_path), "utf-8")

    assert "\r" not in content
    assert content.splitlines() == _CP1252_LINES


def test_read_file_primary_path_normalizes_crlf(tmp_path: Path) -> None:
    """Control: the primary open() path already normalizes; both paths must agree."""
    lines = ["import os", "", "def f():", "    return 1"]
    file_path = tmp_path / "config_utf8.py"
    file_path.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))

    content = FileUtils.read_file(str(file_path), "utf-8")

    assert "\r" not in content
    assert content.splitlines() == lines


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        pytest.param("FreeBSD", "amd64", PlatformId.FREEBSD_x64, id="freebsd-amd64"),
        pytest.param("FreeBSD", "arm64", PlatformId.FREEBSD_arm64, id="freebsd-arm64"),
    ],
)
def test_get_platform_id_freebsd(system: str, machine: str, expected: PlatformId) -> None:
    """FreeBSD should resolve to a freebsd platform id."""
    with (
        patch("solidlsp.ls_utils.platform.system", return_value=system),
        patch("solidlsp.ls_utils.platform.machine", return_value=machine),
        patch("solidlsp.ls_utils.platform.architecture", return_value=("64bit",)),
    ):
        assert PlatformUtils.get_platform_id() is expected


def test_get_platform_id_freebsd_i386_raises() -> None:
    """32-bit FreeBSD was deprecated with the release of FreeBSD 15.0 and must fail with the standard error."""
    with (
        patch("solidlsp.ls_utils.platform.system", return_value="FreeBSD"),
        patch("solidlsp.ls_utils.platform.machine", return_value="i386"),
        patch("solidlsp.ls_utils.platform.architecture", return_value=("32bit",)),
    ):
        with pytest.raises(SolidLSPException, match="Unknown platform"):
            PlatformUtils.get_platform_id()


def test_get_platform_id_unknown_platform_still_raises() -> None:
    """Platforms without an explicit mapping must keep failing explicitly."""
    with (
        patch("solidlsp.ls_utils.platform.system", return_value="SunOS"),
        patch("solidlsp.ls_utils.platform.machine", return_value="i86pc"),
        patch("solidlsp.ls_utils.platform.architecture", return_value=("64bit",)),
    ):
        with pytest.raises(SolidLSPException):
            PlatformUtils.get_platform_id()

def test_read_file_binary_is_skipped_without_encoding_detection(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """
    Undecodable binary files (e.g. a .png swept up by a scan of non-code files) must still raise, but
    without an entry in the error log and without the cost of charset detection, which cannot help.
    """
    file_path = tmp_path / "icon.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 4)

    with caplog.at_level(logging.DEBUG), patch("charset_normalizer.from_path") as from_path:
        with pytest.raises(UnicodeDecodeError):
            FileUtils.read_file(str(file_path), "utf-8")

    from_path.assert_not_called()
    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
    assert any("icon.png" in r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG)


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"])
def test_read_file_bom_encoded_text_is_not_mistaken_for_binary(tmp_path: Path, encoding: str) -> None:
    """UTF-16/32 text contains NUL bytes, so the binary check must defer to the BOM and let the fallback run."""
    lines = ["import os", "", "def f():", "    return 1"]
    file_path = tmp_path / f"config_{encoding}.py"
    bom = {"utf-16-le": codecs.BOM_UTF16_LE, "utf-16-be": codecs.BOM_UTF16_BE}.get(encoding) or (
        codecs.BOM_UTF32_LE if encoding == "utf-32-le" else codecs.BOM_UTF32_BE
    )
    file_path.write_bytes(bom + "\r\n".join(lines).encode(encoding))

    assert not FileUtils.is_binary_file(str(file_path))
    assert FileUtils.read_file(str(file_path), "utf-8").splitlines() == lines
