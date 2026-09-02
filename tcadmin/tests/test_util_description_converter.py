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


def test_description_converter_empty_string(appconfig):
    "An empty description results in just the prefix, and has_content is False"
    appconfig.description_prefix = "I AM A PREFIX\n\n"
    descr = description_converter("")
    assert descr == "I AM A PREFIX\n\n"
    assert descr.has_content is False


def test_description_converter_has_content(appconfig):
    "A real description has has_content set to True"
    appconfig.description_prefix = "I AM A PREFIX\n\n"
    descr = description_converter("I am a description")
    assert descr.has_content is True


def test_description_converter_has_content_survives_reconversion(appconfig):
    "has_content is preserved when an already-converted description is re-converted"
    appconfig.description_prefix = "I AM A PREFIX\n\n"
    empty = description_converter("")
    assert empty.has_content is False
    # re-converting an already-prefixed (and thus non-empty) string must not
    # flip has_content to True just because the string itself is now truthy
    assert description_converter(empty).has_content is False

    real = description_converter("I am a description")
    assert real.has_content is True
    assert description_converter(real).has_content is True
