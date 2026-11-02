from django.core.exceptions import ValidationError

EXTENSIONS = ["mp4", "mp3", "JPG", "jpg", "jpeg", "png", "PNG"]
FILE_SIZE = 1024 * 1024 * 10


def size_validation(file):
    return file.size <= FILE_SIZE


def ext_validation(file):
    file_extension = file.name.split(".")[-1] if "." in file.name else ""
    return file_extension in EXTENSIONS


def file_validation(file):
    if not size_validation(file):
        raise ValidationError(f"the size limit is {FILE_SIZE}")

    if not ext_validation(file):
        raise ValidationError("the file extension is not allowed ")

    return file
