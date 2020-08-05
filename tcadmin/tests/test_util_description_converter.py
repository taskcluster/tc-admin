import pytest


from tcadmin.resources.util import description_converter


pytestmark = pytest.mark.usefixtures("appconfig")


def test_description_converter(appconfig):
    "Descriptions are prefixed"
    appconfig.description_prefix = "I AM A PREFIX\n\n"
    assert (
        description_converter("I am a description")
        == "I AM A PREFIX\n\nI am a description"
    )


def test_description_converter_idempotent(appconfig):
    "Descriptions are prefixed only once"
    appconfig.description_prefix = "I AM A PREFIX\n\n"
    descr = "I am a description"
    descr = description_converter(descr)
    print(descr)
    descr = description_converter(descr)
    print(descr)
    assert descr == "I AM A PREFIX\n\nI am a description"
