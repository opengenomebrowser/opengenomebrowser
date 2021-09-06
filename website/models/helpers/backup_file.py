import os.path
from os import path, makedirs, remove
from shutil import move
from datetime import datetime
import json


def is_empty(string: str) -> bool:
    return string.strip() == ''


def read_file_or_default(file: str, default=None, default_if_empty: bool = False) -> str:
    if not path.isfile(file):
        return default
    with open(file) as f:
        content = f.read()
        if default_if_empty and is_empty(content):
            return default
        return content


def backup_file(file: str, user: str = None) -> str:
    """
    Move the file into a .bkp subdir.

    :param file: path to file
    :param user: user who did the change (must be alphanumeric)
    :returns: path to backup file
    """
    if user is None:
        user = 'nouser'

    assert path.isfile(file), f'File does not exist: {file}'
    assert user.isalnum(), f'File does not exist: {file}'
    dirname = path.dirname(file)
    basename = path.basename(file)
    bkp_dir = f'{dirname}/.bkp'

    # create backup dir
    makedirs(bkp_dir, exist_ok=True)

    # path to backup file
    bkp_file = f'{bkp_dir}/{datetime.now().strftime("%Y_%b_%d_%H_%M_%S")}_{user}_{basename}'

    # move file
    move(src=file, dst=bkp_file)

    return bkp_file


def overwrite_with_backup(file: str, content, user: str = None, delete_if_empty=False) -> None:
    """
    Create backup of the file, replace it with new content.

    :param file: path to file
    :param content: new content: str, dict or list
    :param user: user who did the change (must be alphanumeric)
    :returns: path to backup file
    """
    if type(content) in [dict, list]:
        content = json.dumps(content, indent=4)

    assert type(content) is str, f'Error in overwrite_with_backup: content must be string, dict or list!'

    if path.isfile(file):
        backup_file(file=file, user=user)

    if delete_if_empty and is_empty(content):
        return

    with open(file, 'w') as f:
        f.write(content)
