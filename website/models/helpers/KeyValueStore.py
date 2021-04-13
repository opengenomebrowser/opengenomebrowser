import os
import json


class KeyValueStore:
    _file: str = None
    _model = None
    _key: str = None
    _key_isint: bool = False
    _value: str = None

    def __init__(self):
        _dict = self.get_dict()
        with open(self._file, 'w') as f:
            json.dump(_dict, f, indent=4)

        for _tmp in [self._file, self._model, self._key, self._value]:
            assert _tmp is not None, 'Error in KeyValueStore: poorly initialized'

    def get_dict(self) -> dict:
        dict_ = {}
        if os.path.isfile(self._file):
            dict_ = json.load(open(self._file))
            if self._key_isint:
                dict_ = {int(a): b for a, b in dict_.items()}
        # overwrite with values from database
        dict_.update(dict(self._model.objects.all().values_list(self._key, self._value)))
        return dict_

    def get_key(self, key) -> str:
        tmp_dict = self.get_dict()
        return tmp_dict[key]

    def set_key(self, key, value):
        tmp_dict = self.get_dict()
        tmp_dict[key] = value
        json.dump(tmp_dict, open(self._file, 'w'), indent=4)
