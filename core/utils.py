EXTENSIONS = ["mp4", "mp3", "JPG", "jpg", "png", "PNG"]
FILE_SIZE = 1024 * 1024 * 10


def validate_file_size(file):
    return file.size <= FILE_SIZE


def file_validation(file):
    file_extension = file.name.split(".")[-1] if "." in file.name else ""
    return file_extension in EXTENSIONS
