import pytest
if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.sudsobject import Object
from suds.sudsobject import asdict, recursive_asdict


# test_suds_functions.py

def test_asdict():
    # Create a suds object
    sobject = Object()
    sobject.name = "John Doe"
    sobject.age = 30
    sobject.children = []

    # Call the asdict function
    result = asdict(sobject)

    # Assert the expected result
    expected = {
        'name': 'John Doe',
        'age': 30,
        'children': []
    }
    assert result == expected


def test_recursive_asdict():
    # Create a suds object with nested objects
    outer_object = Object()
    outer_object.name = "John Doe"
    outer_object.age = 30
    outer_object.children = []

    inner_object = Object()
    inner_object.name = "Jane Doe"
    inner_object.age = 25
    inner_object.children = []

    outer_object.children.append(inner_object)

    grandchild_object = Object()
    grandchild_object.name = "Baby Doe"
    grandchild_object.age = 1

    inner_object.children.append(grandchild_object)

    # Call the recursive_asdict function
    result = asdict(outer_object,True)

    # Assert the expected result
    expected = {
        'name': 'John Doe',
        'age': 30,
        'children': [
            {
                'name': 'Jane Doe',
                'age': 25,
                'children': [
                    {
                        'name': 'Baby Doe',
                        'age': 1
                    }
                ]
            }
        ]
    }
    assert result == expected

