import base64  # (may not need if just using x.decode*)
import umsgpack
from collections import OrderedDict
import json
"""
Maps must contain keys in lexicographic order;
Maps must omit key-value pairs where the value is a zero-value;
Positive integer values must be encoded as "unsigned" in msgpack,
    regardless of whether the value space is semantically signed
    or unsigned;
Integer values must be represented in the shortest possible encoding;
Binary arrays must be represented using the "bin" format family
    (that is, use the most recent version of msgpack rather than the
    older msgpack version that had no "bin" family).
"""


def msgpack_encode(obj):
    if not isinstance(obj, dict):
        obj = obj.dictify()
    od = OrderedDict()
    for key in obj:
        if obj[key]:
            od[key] = obj[key]
    return base64.b64encode(umsgpack.dumps(od)).decode()


def json_encode(obj):
    if not isinstance(obj, dict):
        obj = obj.dictify()
    to_delete = []
    for key in obj:
        if (not obj[key]):
            to_delete.append(key)
    for key in to_delete:
        del obj[key]

    return json.dumps(obj, sort_keys=True)
