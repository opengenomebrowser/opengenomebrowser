import os
import requests
import tarfile


def install():
    path = os.path.dirname(os.path.abspath(__file__))
    orthofinder_bin = F'{path}/OrthoFinder/orthofinder'

    if os.path.isfile(orthofinder_bin):
        print('orthofinder is already installed!')
        return

    url = 'https://github.com/davidemms/OrthoFinder/releases/download/2.3.12/OrthoFinder.tar.gz'

    print(F'downloading orthofinder: {url}')
    f = requests.get(url, allow_redirects=True)

    tmp_path = '/tmp/OrthoFinder.tar.gz'
    open(tmp_path, 'wb').write(f.content)

    print('extracting orthofinder...')
    with tarfile.open(tmp_path) as tar:
        tar.extractall(path=path)

    os.remove(tmp_path)

    assert os.path.isfile(orthofinder_bin), F'Installation of OrthoFinder failed! File is missing: {orthofinder_bin}'

    return


if __name__ == '__main__':
    install()
