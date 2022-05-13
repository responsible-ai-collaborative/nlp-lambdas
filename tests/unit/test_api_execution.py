import os.path
from ..helpers import apitest

path_to_project_root = "."
json_dir_from_project_root = ["tests", "unit", "testing_materials"]

# Shorthand helper for creating paths to test json files
def mkpath(json_filename: str):
    return os.path.join(path_to_project_root,
                        *json_dir_from_project_root,
                        json_filename)

def test_good_execution():
    assert apitest.api_full_test_run(1, mkpath("lambda_test_request_incident_1.json"))
    assert apitest.api_full_test_run(15, mkpath("lamdba_test_request_incident_15.json"))
    assert apitest.api_full_test_run(10, mkpath("lamdba_test_request_incident_10.json"))

def test_incorrect_value():
    assert not apitest.api_full_test_run(-5, mkpath("lamdba_test_request_incident_15.json"))

# Additional tests might include
#   - checking that bestOf=N parameter correctly gives N results
#   - looking for custom exceptions on bad inputs