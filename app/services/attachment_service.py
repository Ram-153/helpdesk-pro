import os
import uuid

from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "txt",
    "doc",
    "docx",
    "xls",
    "xlsx",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def get_file_extension(filename):
    if "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def is_allowed_file(filename):
    extension = get_file_extension(filename)

    return extension in ALLOWED_EXTENSIONS


def generate_stored_filename(filename):
    extension = get_file_extension(filename)

    return f"{uuid.uuid4().hex}.{extension}"


def save_attachment(file, upload_directory):
    if not file or not file.filename:
        raise ValueError("No file provided")

    original_filename = secure_filename(file.filename)

    if not original_filename:
        raise ValueError("Invalid filename")

    if not is_allowed_file(original_filename):
        raise ValueError("File type is not allowed")

    file.stream.seek(0, os.SEEK_END)
    file_size = file.stream.tell()
    file.stream.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 5 MB limit")

    os.makedirs(upload_directory, exist_ok=True)

    stored_filename = generate_stored_filename(original_filename)

    file_path = os.path.join(
        upload_directory,
        stored_filename,
    )

    file.save(file_path)

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "file_size": file_size,
        "mime_type": file.mimetype or "application/octet-stream",
    }