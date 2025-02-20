import os


def check_file_exists(file_path: str):
    return os.path.exists(file_path)
