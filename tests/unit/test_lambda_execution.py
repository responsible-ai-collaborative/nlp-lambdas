import pytest
import os.path
from ..helpers import testrun
from ..helpers.custom_exceptions \
    import (
        JsonException,
        SamOutputException
    )

path_to_project_root = "."
json_dir_from_project_root = ["tests", "unit", "testing_materials"]

# Shorthand helper for creating paths to test json files
def mkpath(json_filename: str):
    return os.path.join(path_to_project_root,
                        *json_dir_from_project_root,
                        json_filename)

def test_good_execution():
    assert testrun.run_text_to_db_similar_tests(1, mkpath("lambda_test_request_incident_1.json"))
    assert testrun.run_text_to_db_similar_tests(15, mkpath("lamdba_test_request_incident_15.json"))
    assert testrun.run_text_to_db_similar_tests(10, mkpath("lamdba_test_request_incident_10.json"))

def test_incorrect_value():
    assert not testrun.run_text_to_db_similar_tests(-5, mkpath("lamdba_test_request_incident_15.json"))

def test_json_input_syntax_error():
    with pytest.raises(JsonException):
        testrun.run_text_to_db_similar_tests(1, mkpath("lamdba_bad_test_request_bad_syntax.json"))

def test_missing_required_input_field():
    with pytest.raises(SamOutputException):
        testrun.run_text_to_db_similar_tests(1, mkpath("lamdba_bad_test_request_missing_input.json"))

# Additional tests might include
#   - checking that bestOf=N parameter correctly gives N results