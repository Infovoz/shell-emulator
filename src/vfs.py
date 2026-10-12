"""In-memory virtual file system loaded from ZIP archive."""

import io
import os
import zipfile

PATH_SEP = "/"


class VirtualFileSystem:
    """Represents an in-memory virtual filesystem loaded from ZIP."""

    def __init__(self, zip_path: str | None = None) -> None:
        """Initialize VFS from file or fallback to memory default."""
        self.files: dict[str, bytes] = {}
        self.directories: set[str] = {PATH_SEP}
        self.current_dir = PATH_SEP
        self.load_error: str | None = None

        if zip_path:
            self._load_from_zip(zip_path)
        else:
            self._init_default_vfs()

    def _normalize_path(self, path: str) -> str:
        """Normalize VFS path to UNIX format."""
        cleaned = path.replace("\\", PATH_SEP).strip()
        parts = [p for p in cleaned.split(PATH_SEP) if p and p != "."]
        return PATH_SEP + PATH_SEP.join(parts)

    def _init_default_vfs(self) -> None:
        """Populate initial in-memory directory tree with sample data."""
        self.directories.update({
            "/home",
            "/home/user",
            "/home/user/docs",
            "/etc",
            "/bin",
        })
        self.files["/home/user/readme.txt"] = (
            b"Welcome to in-memory VFS default tree!\n"
        )
        self.files["/etc/config.cfg"] = b"theme=dark\nmode=interactive\n"

    def _load_from_zip(self, zip_path: str) -> None:
        """Load directory and file hierarchy from ZIP archive in memory."""
        if not os.path.exists(zip_path):
            self.load_error = f"VFS file not found: {zip_path}"
            self._init_default_vfs()
            return

        try:
            with open(zip_path, "rb") as archive_stream:
                raw_bytes = io.BytesIO(archive_stream.read())
            with zipfile.ZipFile(raw_bytes, "r") as archive:
                for entry in archive.infolist():
                    norm_path = self._normalize_path(entry.filename)
                    if entry.is_dir():
                        self.directories.add(norm_path)
                    else:
                        parent = self._normalize_path(
                            os.path.dirname(entry.filename)
                        )
                        self.directories.add(parent)
                        self.files[norm_path] = archive.read(entry.filename)
        except zipfile.BadZipFile:
            self.load_error = f"Invalid ZIP archive format: {zip_path}"
            self._init_default_vfs()

    def resolve_path(self, target_path: str) -> str:
        """Resolve relative or absolute path against current working dir."""
        if target_path.startswith(PATH_SEP):
            raw = target_path
        else:
            raw = os.path.join(self.current_dir, target_path)

        norm = self._normalize_path(raw)
        tokens = [t for t in norm.split(PATH_SEP) if t]
        stack: list[str] = []
        for token in tokens:
            if token == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(token)
        return PATH_SEP + PATH_SEP.join(stack)