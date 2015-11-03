import datetime
import json

import dashi.config


class MyEncoder(json.JSONEncoder):
    def default(self, obj): # pylint: disable=method-hidden
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, dashi.config.User):
            return obj.name
        elif isinstance(obj, dashi.config.Repository):
            return obj.name
        return json.JSONEncoder.default(self, obj)

def dump(obj, f):
    json.dump(obj, f, cls=MyEncoder)
