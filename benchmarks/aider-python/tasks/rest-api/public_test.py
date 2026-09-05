# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/rest-api/canonical-data.json
# File last updated on 2023-07-19

import json
import unittest

from rest_api import (
    RestAPI,
)


class RestApiTest(unittest.TestCase):
    def test_no_users(self):
        database = {"users": []}
        api = RestAPI(database)

        response = api.get("/users")
        expected = {"users": []}
        self.assertDictEqual(json.loads(response), expected)


if __name__ == "__main__":
    unittest.main()
