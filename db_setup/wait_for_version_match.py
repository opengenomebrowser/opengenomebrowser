import os
from time import sleep
from opengenomebrowser_tools.utils import get_folder_structure_version

EXPECTED_VERSION = 2
FOLDER_STRUCTURE = os.environ.get('FOLDER_STRUCTURE', '/folder_structure')
VERSION_FILE = f'{FOLDER_STRUCTURE}/version.json'


def wait_for_version_match():
    first_time = True
    while True:
        version = get_folder_structure_version(folder_structure_dir=FOLDER_STRUCTURE)

        if version == EXPECTED_VERSION:
            break

        if first_time:
            print(
                f'\n\nERROR!\n'
                f'The folder structure needs to be updated to match OpenGenomeBrowser code.\n'
                f'Current version: {version}, expected: {EXPECTED_VERSION}\n'
                f'Use the script update_folder_structure from the package opengenomebrowser_tools to perform the upgrade!'
            )
        first_time = False
        sleep(10)

    print(f'Folder structure version matches: {EXPECTED_VERSION}')


if __name__ == "__main__":
    wait_for_version_match()
