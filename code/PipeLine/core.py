import os
import sys
import tempfile
from pathlib import Path

from werkzeug.utils import secure_filename

COMPRESSOR_DIR = Path(__file__).resolve().parents[1] / "compressor"
sys.path.insert(0, str(COMPRESSOR_DIR))

from compress import compress_file
from descompress import _parse_ppl, descompress


UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)


def get_original_name(ppl_path: Path):
    try:
        nome, _, _, _ = _parse_ppl(ppl_path.read_bytes())
        return nome
    except Exception:
        return ppl_path.name


def list_files():
    files = []

    for path in UPLOAD_FOLDER.iterdir():
        if path.is_file():
            files.append({
                "display": get_original_name(path),
                "storage": path.name
            })

    return sorted(files, key=lambda x: x["display"].lower())


def save_and_compress(file_storage):
    original = file_storage.filename
    if not original:
        return None

    filename = secure_filename(original)
    if not filename:
        return None

    original_path = Path(filename)
    if original_path.suffix.lower() == ".ppl":
        output_name = filename + ".ppl"
    else:
        output_name = original_path.with_suffix(".ppl").name

    output_path = UPLOAD_FOLDER / output_name
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        dir=UPLOAD_FOLDER,
        suffix=original_path.suffix,
    )
    temp_path = Path(temp_file.name)
    temp_file.close()

    file_storage.save(temp_path)

    try:
        compress_file(temp_path, output_path, original_name=filename)
    finally:
        temp_path.unlink(missing_ok=True)

    return output_path.name


def get_file(path_name: str):
    return UPLOAD_FOLDER / path_name


def get_download_payload(path_name: str):
    if Path(path_name).name != path_name:
        return None

    path = UPLOAD_FOLDER / path_name
    if not path.is_file():
        return None

    data = path.read_bytes()
    try:
        original_name, content = descompress(data)
    except Exception:
        return path.name, data

    download_name = Path(original_name).name or path.name
    return download_name, content
