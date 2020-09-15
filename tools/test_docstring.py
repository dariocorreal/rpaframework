import json
import docstring

example = """

This is an example of Google style.
This block continues.

An empty line here.

Note:
    This is a note

See also:
    https://www.robocorp.com

Args:
    param1 (int): This is the first param.
    param2 (bool): This is a second param.
       test a continuation?

Some more body in the middle?
Does this work?

Returns:
    bool: This is one with a type
    This is a description of what is returned.

Example:
    Cool beans    arg=value
    Another one    Stuff    Thing

Examples:
    Hello world invocation

Raises:
    KeyError: Raises an exception.

"""

doc = docstring.Docstring()
output = doc.parse(example)
print(json.dumps(output, indent=4))
