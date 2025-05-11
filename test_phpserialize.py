# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "phpserialize",
# ]
# ///
import phpserialize

def test_php_unserialize_simple_array():
    # Example PHP serialized array: a:2:{i:0;s:4:"test";i:1;s:3:"foo";}
    php_serialized = 'a:2:{i:0;s:4:"test";i:1;s:3:"foo";}'
    result = phpserialize.loads(php_serialized.encode('utf-8'), decode_strings=True)
    assert result == {0: "test", 1: "foo"}


def test_php_unserialize_list_like_array():
    # Helper to convert dict with sequential integer keys to list
    def dict_to_list_if_sequential(d):
        if isinstance(d, dict):
            keys = list(d.keys())
            if keys == list(range(len(keys))):
                return [d[k] for k in sorted(d.keys())]
        return d

    php_serialized = 'a:3:{i:0;s:3:"one";i:1;s:3:"two";i:2;s:5:"three";}'
    result = phpserialize.loads(php_serialized.encode('utf-8'), decode_strings=True)
    as_list = dict_to_list_if_sequential(result)
    assert as_list == ["one", "two", "three"]


def test_php_unserialize_dict():
    # Example PHP serialized dict: a:2:{s:3:"bar";s:3:"baz";s:3:"foo";s:3:"qux";}
    php_serialized = 'a:2:{s:3:"bar";s:3:"baz";s:3:"foo";s:3:"qux";}'
    result = phpserialize.loads(php_serialized.encode('utf-8'), decode_strings=True)
    assert result == {"bar": "baz", "foo": "qux"}


def test_php_unserialize_scalar():
    php_serialized = 's:5:"hello";'
    result = phpserialize.loads(php_serialized.encode('utf-8'), decode_strings=True)
    assert result == "hello" 