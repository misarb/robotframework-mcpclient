"""Unit tests for the SDK-shape normalisation in _convert.

These matter more than they look: the whole point of the module is that a
rename in the MCP SDK does not reach the user's test suites. The camelCase
cases below are the shapes older SDK versions produce.
"""

from types import SimpleNamespace

import pytest

from MCPClientLibrary import _convert as convert
from MCPClientLibrary.errors import MCPLibraryError


def text_block(text):
    return SimpleNamespace(type="text", text=text)


class TestIsError:
    def test_snake_case_flag(self):
        assert convert.is_error(SimpleNamespace(is_error=True)) is True
        assert convert.is_error(SimpleNamespace(is_error=False)) is False

    def test_camel_case_flag_from_older_sdks(self):
        assert convert.is_error(SimpleNamespace(isError=True)) is True

    def test_dict_results(self):
        assert convert.is_error({"isError": True}) is True
        assert convert.is_error({"is_error": True}) is True

    def test_missing_flag_means_success(self):
        assert convert.is_error(SimpleNamespace()) is False

    def test_none_flag_means_success(self):
        assert convert.is_error(SimpleNamespace(is_error=None)) is False


class TestToolFields:
    def test_tool_name(self):
        assert convert.tool_name(SimpleNamespace(name="get_weather")) == "get_weather"

    def test_tool_without_a_name_is_an_error(self):
        with pytest.raises(MCPLibraryError, match="has no name"):
            convert.tool_name(SimpleNamespace())

    def test_input_schema_under_either_spelling(self):
        schema = {"type": "object"}
        assert convert.input_schema(SimpleNamespace(input_schema=schema)) == schema
        assert convert.input_schema(SimpleNamespace(inputSchema=schema)) == schema

    def test_missing_input_schema(self):
        assert convert.input_schema(SimpleNamespace()) is None

    def test_schema_required(self):
        tool = SimpleNamespace(input_schema={"required": ["city"]})
        assert convert.schema_required(tool) == ["city"]

    def test_schema_required_without_a_schema(self):
        assert convert.schema_required(SimpleNamespace()) == []

    def test_schema_required_without_a_required_list(self):
        assert convert.schema_required(SimpleNamespace(input_schema={"type": "object"})) == []

    def test_schema_properties(self):
        tool = SimpleNamespace(input_schema={"properties": {"city": {"type": "string"}}})
        assert list(convert.schema_properties(tool)) == ["city"]

    def test_schema_properties_without_a_schema(self):
        assert convert.schema_properties(SimpleNamespace()) == {}


class TestText:
    def test_all_text_joins_every_block(self):
        result = SimpleNamespace(content=[text_block("first"), text_block("second")])
        assert convert.all_text(result) == "first\nsecond"

    def test_all_text_skips_non_text_blocks(self):
        result = SimpleNamespace(
            content=[text_block("caption"), SimpleNamespace(type="image", data="...")]
        )
        assert convert.all_text(result) == "caption"

    def test_all_text_of_an_empty_result(self):
        assert convert.all_text(SimpleNamespace(content=[])) == ""

    def test_all_text_reads_resource_contents_too(self):
        result = SimpleNamespace(contents=[text_block("the docs")])
        assert convert.all_text(result) == "the docs"

    def test_content_blocks_of_an_empty_result(self):
        assert convert.content_blocks(SimpleNamespace()) == []


class TestStructuredContent:
    def test_either_spelling(self):
        data = {"temperature": 18}
        assert convert.structured_content(SimpleNamespace(structured_content=data)) == data
        assert convert.structured_content(SimpleNamespace(structuredContent=data)) == data

    def test_missing_is_none(self):
        assert convert.structured_content(SimpleNamespace()) is None


class TestPromptMessages:
    def test_message_with_a_single_content_block(self):
        message = SimpleNamespace(content=text_block("Write a report."))
        assert convert.message_text(message) == "Write a report."

    def test_message_with_a_list_of_blocks(self):
        message = SimpleNamespace(content=[text_block("one"), text_block("two")])
        assert convert.message_text(message) == "one\ntwo"

    def test_message_without_content(self):
        assert convert.message_text(SimpleNamespace()) == ""

    def test_prompt_messages_of_an_empty_result(self):
        assert convert.prompt_messages(SimpleNamespace()) == []


class TestResourceUri:
    def test_uri_is_stringified(self):
        # The SDK models URIs as objects, not strings.
        class Uri:
            def __str__(self):
                return "docs://usage"

        assert convert.resource_uri(SimpleNamespace(uri=Uri())) == "docs://usage"


class TestToDict:
    def test_plain_values_pass_through(self):
        assert convert.to_dict("text") == "text"
        assert convert.to_dict(42) == 42

    def test_lists_are_converted_item_by_item(self):
        assert convert.to_dict([{"a": 1}]) == [{"a": 1}]

    def test_pydantic_like_objects_are_dumped(self):
        class Model:
            def model_dump(self, mode=None, by_alias=None):
                return {"name": "get_weather"}

        assert convert.to_dict(Model()) == {"name": "get_weather"}

    def test_nested_dicts_are_converted(self):
        class Model:
            def model_dump(self, mode=None, by_alias=None):
                return {"name": "echo"}

        assert convert.to_dict({"tool": Model()}) == {"tool": {"name": "echo"}}
