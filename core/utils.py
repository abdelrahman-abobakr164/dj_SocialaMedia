EXTENSIONS = ["mp4", "mp3", "JPG", "jpg", "png", "PNG"]
FILE_SIZE = 1024 * 1024 * 10


def validate_file_size(file):
    return file.size <= FILE_SIZE


def file_validation(file_name):
    file_extension = file_name.split(".")[-1] if "." in file_name else ""
    return file_extension in EXTENSIONS
