"""Script for creating test ZIP files with hierarchical structure."""

import io
import zipfile


def create_sample_zip(filename: str) -> None:
    """Create ZIP archive with deeply nested folders and text files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "level1/level2/level3/deep.txt",
            "Deep content here\n",
        )
        archive.writestr("level1/level2/notes.txt", "Second level note\n")
        archive.writestr("level1/hello.txt", "First level hello\n")
        archive.writestr("root.txt", "Archive root file\n")

    with open(filename, "wb") as output_file:
        output_file.write(buffer.getvalue())


if __name__ == "__main__":
    create_sample_zip("test_vfs.zip")
    print("Created test_vfs.zip with 3 levels of nesting.")