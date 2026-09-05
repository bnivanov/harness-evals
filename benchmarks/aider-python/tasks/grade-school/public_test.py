# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/grade-school/canonical-data.json
# File last updated on 2023-07-19

import unittest

from grade_school import (
    School,
)


class GradeSchoolTest(unittest.TestCase):
    def test_roster_is_empty_when_no_student_is_added(self):
        school = School()
        expected = []

        self.assertEqual(school.roster(), expected)


if __name__ == "__main__":
    unittest.main()
