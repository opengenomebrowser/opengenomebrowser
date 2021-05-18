import logging
import os
import json
import shutil
import pickle
import time
from hashlib import sha1
from datetime import timedelta, datetime

WAIT_TOLERANCE = timedelta(seconds=10)

"""
CACHE_DIR/:                 cache_dir
CACHE_DIR/function/:        cache_fn_dir
CACHE_DIR/function/<hash>/: cache_res_dir
"""


def _dump_res(cache_res_dir, res) -> None:
    with open(f'{cache_res_dir}/res.pickle', 'wb') as f:
        pickle.dump(res, f)


def _load_res(cache_res_dir) -> tuple:
    with open(f'{cache_res_dir}/res.pickle', 'rb') as f:
        res = pickle.load(f)
    return res


def _load_timestamp(cache_res_dir: str) -> datetime:
    with open(f'{cache_res_dir}/timestamp.txt') as f:
        timestamp = datetime.fromisoformat(f.read().strip())
    return timestamp


def _dump_timestamp(cache_res_dir: str) -> None:
    timestamp = datetime.now().isoformat()
    with open(f'{cache_res_dir}/timestamp.txt', 'w') as f:
        f.write(timestamp)


def clear_cache(cache_fn_dir: str, maxsize: int) -> None:
    if not os.path.isdir(cache_fn_dir):
        return

    to_remove = sorted(
        [entry for entry in os.scandir(cache_fn_dir)],
        key=lambda entry: os.path.getctime(entry.path),
        reverse=True
    )[maxsize:]

    for entry in to_remove:
        entry: os.DirEntry
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                os.remove(entry)
        except Exception as e:
            logging.warning(f'Could not delete cache: {dir=} {e=}')


def _hash(args, kwargs):
    try:
        args_hash = sha1(json.dumps(args, sort_keys=True).encode("utf-8")).hexdigest()
    except TypeError as e:
        raise type(e)(str(e) + f' - Could not hash args. ({args=})')

    try:
        kwargs_hash = sha1(json.dumps(kwargs, sort_keys=True).encode("utf-8")).hexdigest()
    except TypeError as e:
        raise type(e)(str(e) + f' - Could not hash kwargs. ({kwargs=})')

    return f'{args_hash}:{kwargs_hash}'


def load_cache_or_run(cache_dir: str, wait_tolerance: timedelta, add_cache_dir_kwarg: bool, maxsize: int, func, args, kwargs):
    cache_fn_dir = os.path.join(cache_dir, f'{func.__module__}.{func.__name__}')
    hash = _hash(args, kwargs)
    cache_res_dir = os.path.join(cache_fn_dir, hash)

    if os.path.isdir(cache_res_dir):
        print(f'----- ogb cache : load ----- {cache_fn_dir}/{hash}')
        try:
            res = _load_res(cache_res_dir)
        except Exception:
            time.sleep(wait_tolerance.total_seconds())
            res = _load_res(cache_res_dir)

        # only update timestamp if cache successfully read
        _dump_timestamp(cache_res_dir)

    else:
        print(f'----- ogb cache : run  ----- {cache_fn_dir}/{hash}')
        os.makedirs(cache_res_dir)
        try:
            _dump_timestamp(cache_res_dir)

            # run function
            if add_cache_dir_kwarg:
                res = func(*args, **kwargs, cache_res_dir=cache_res_dir)
            else:
                res = func(*args, **kwargs)

            # save output to cache

            _dump_res(cache_res_dir, res)
        except Exception as e:
            logging.warning(f'Failed to create cache! {cache_res_dir=}')
            shutil.rmtree(cache_res_dir)
            raise e

    # delete old files
    clear_cache(cache_fn_dir=cache_fn_dir, maxsize=maxsize)

    return res


def ogb_cache(
        cache_root: str,
        maxsize: int,
        wait_tolerance: timedelta = WAIT_TOLERANCE,
        add_cache_dir_kwarg: bool = False
):
    """
    This is a decorator function. Example usage:

    @ogb_cache(cache_root=/tmp, maxsize=2, wait_tolerance=timedelta(seconds=30))
    def go_2(cache_res_dir: str):
        ...

    :param cache_root: root directory of the cache. will create a subfolder for each cached function
    :param maxsize: max entries in the cache
    :param wait_tolerance: if cache cannot be loaded, try again after wait_tolerance
    :param add_cache_dir_kwarg: if true, add kwarg to function: {cache_res_dir: /cache_root/function/hash}
    """
    cache_dir = os.path.expanduser(cache_root)
    os.makedirs(cache_dir, exist_ok=True)

    def inner(func):
        def wrapper(*args, **kwargs):
            res = load_cache_or_run(
                cache_dir=cache_dir, wait_tolerance=wait_tolerance, add_cache_dir_kwarg=add_cache_dir_kwarg, maxsize=maxsize,
                func=func, args=args, kwargs=kwargs
            )
            return res

        return wrapper

    return inner


if __name__ == '__main__':
    from OpenGenomeBrowser.settings import CACHE_DIR, CACHE_MAXSIZE


    @ogb_cache(cache_root=CACHE_DIR, maxsize=2, add_cache_dir_kwarg=True, wait_tolerance=timedelta(seconds=1))
    def go(a, cache_res_dir: str):
        assert os.path.isdir(cache_res_dir)
        return a


    for i in [1, 2, 3, 2, 3, 2]:
        a = go(i)
