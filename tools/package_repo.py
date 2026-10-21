"""Create a Linux-ready source ZIP, excluding local state and generated reports."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from hashlib import sha256
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {".git", ".venv", "__pycache__", "analysis-results", "test-results", ".pytest_cache",
           "node_modules", ".DS_Store"}


def package(destination):
    subprocess.run([sys.executable, str(ROOT / "tools/check_repo.py")], check=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(part in EXCLUDE for part in relative.parts) or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise ValueError(f"Symlinks are not included: {relative}")
            info = ZipInfo(f"{ROOT.name}/{relative.as_posix()}")
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=6)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert all(n.startswith("CIBB_2026/") for n in archive.namelist())
        count = len(archive.namelist())
    digest = sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="utf-8", newline="\n")
    print(f"{destination.name}: {count} files; {destination.stat().st_size / 1024**2:.2f} MiB")
    print("SHA-256:", digest)


if __name__ == "__main__":
    package(ROOT.parent / "CIBB_2026.zip")
