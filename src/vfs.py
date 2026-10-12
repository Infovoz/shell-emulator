"""In-memory virtual file system with shell operations."""

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
        """Normalize VFS path to standard UNIX representation."""
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
            b"Line 1: Welcome to in-memory VFS!\nLine 2: Enjoy using shell.\n"
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
            if self.current_dir == PATH_SEP:
                raw = PATH_SEP + target_path
            else:
                raw = f"{self.current_dir}/{target_path}"

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

    def list_dir(self, target_path: str = "") -> list[str]:
        """List immediate child nodes for specified directory path."""
        resolved = (
            self.resolve_path(target_path) if target_path else self.current_dir
        )
        if resolved not in self.directories:
            raise FileNotFoundError(
                f"ls: cannot access '{target_path}': No such directory"
            )

        entries: set[str] = set()
        prefix = resolved if resolved != PATH_SEP else ""

        for directory in self.directories:
            if directory != resolved and directory.startswith(prefix + PATH_SEP):
                remainder = directory[len(prefix) + 1:].split(PATH_SEP)[0]
                if remainder:
                    entries.add(remainder + "/")

        for file_path in self.files:
            if file_path.startswith(prefix + PATH_SEP):
                remainder = file_path[len(prefix) + 1:].split(PATH_SEP)[0]
                if remainder:
                    if PATH_SEP in file_path[len(prefix) + 1:]:
                        entries.add(remainder + "/")
                    else:
                        entries.add(remainder)

        return sorted(entries)

    def change_dir(self, target_path: str) -> None:
        """Change current directory within in-memory tree."""
        resolved = self.resolve_path(target_path)
        if resolved in self.directories:
            self.current_dir = resolved
        elif resolved in self.files:
            raise NotADirectoryError(f"cd: not a directory: {target_path}")
        else:
            raise FileNotFoundError(
                f"cd: no such file or directory: {target_path}"
            )

    def read_file(self, target_path: str) -> str:
        """Read and decode file contents from memory."""
        resolved = self.resolve_path(target_path)
        if resolved in self.directories:
            raise IsADirectoryError(f"cat: {target_path}: Is a directory")
        if resolved not in self.files:
            raise FileNotFoundError(f"cat: {target_path}: No such file")
        return self.files[resolved].decode("utf-8", errors="replace")

    def read_file_reversed(self, target_path: str) -> str:
        """Read file contents and reverse line order."""
        content = self.read_file(target_path)
        lines = content.splitlines()
        return "\n".join(reversed(lines))

    def copy_item(self, source_path: str, dest_path: str) -> None:
        """Copy in-memory file to destination path without touching disk."""
        src_resolved = self.resolve_path(source_path)
        if src_resolved not in self.files:
            if src_resolved in self.directories:
                raise IsADirectoryError(f"cp: -r not specified: {source_path}")
            raise FileNotFoundError(f"cp: cannot stat '{source_path}': No such file")

        dst_resolved = self.resolve_path(dest_path)
        if dst_resolved in self.directories:
            src_filename = src_resolved.split(PATH_SEP)[-1]
            if dst_resolved == PATH_SEP:
                dst_resolved = PATH_SEP + src_filename
            else:
                dst_resolved = f"{dst_resolved}/{src_filename}"

        parent_dir = self._normalize_path(os.path.dirname(dst_resolved))
        if parent_dir not in self.directories:
            raise FileNotFoundError(
                f"cp: cannot create regular file '{dest_path}': No such directory"
            )

        self.files[dst_resolved] = self.files[src_resolved]