import os
import filetype
from django.core.exceptions import ValidationError

FILE_SIZE = 10 * 1024 * 1024

ALLOWED = {
    "jpg": {"mimes": {"image/jpeg"}, "type": "image"},
    "jpeg": {"mimes": {"image/jpeg"}, "type": "image"},
    "png": {"mimes": {"image/png"}, "type": "image"},
    "mp3": {"mimes": {"audio/mpeg"}, "type": "audio"},
    "mp4": {"mimes": {"video/mp4"}, "type": "video"},
}


def file_validation(file):
    if file.size > FILE_SIZE:
        raise ValidationError(
            f"File too large. Max size is {FILE_SIZE // (1024 * 1024)} MB."
        )

    ext = os.path.splitext(file.name)[1].lstrip(".").lower()
    rule = ALLOWED.get(ext)
    if rule is None:
        raise ValidationError("File extension is not allowed.")

    head = file.read(2048)
    file.seek(0) 
    detected = filetype.guess_mime(head)
    if detected not in rule["mimes"]:
        raise ValidationError("File content does not match its extension.")

    return rule["type"]
