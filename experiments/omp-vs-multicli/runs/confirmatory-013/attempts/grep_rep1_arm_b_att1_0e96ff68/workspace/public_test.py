# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/grep/canonical-data.json
# File last updated on 2023-07-19

import io
import unittest

from grep import (
    grep,
)
from unittest import mock

FILE_TEXT = {
    "iliad.txt": """Achilles sing, O Goddess! Peleus' son;
His wrath pernicious, who ten thousand woes
Caused to Achaia's host, sent many a soul
Illustrious into Ades premature,
And Heroes gave (so stood the will of Jove)
To dogs and to all ravening fowls a prey,
When fierce dispute had separated once
The noble Chief Achilles from the son
Of Atreus, Agamemnon, King of men.\n""",
    "midsummer-night.txt": """I do entreat your grace to pardon me.
I know not by what power I am made bold,
Nor how it may concern my modesty,
In such a presence here to plead my thoughts;
But I beseech your grace that I may know
The worst that may befall me in this case,
If I refuse to wed Demetrius.\n""",
    "paradise-lost.txt": """Of Mans First Disobedience, and the Fruit
Of that Forbidden Tree, whose mortal tast
Brought Death into the World, and all our woe,
With loss of Eden, till one greater Man
Restore us, and regain the blissful Seat,
Sing Heav'nly Muse, that on the secret top
Of Oreb, or of Sinai, didst inspire
That Shepherd, who first taught the chosen Seed\n""",
}


def open_mock(fname, *args, **kwargs):
    try:
        return io.StringIO(FILE_TEXT[fname])
    except KeyError:
        raise RuntimeError(
            "Expected one of {0!r}: got {1!r}".format(list(FILE_TEXT.keys()), fname)
        )


@mock.patch("grep.open", name="open", side_effect=open_mock, create=True)
@mock.patch("io.StringIO", name="StringIO", wraps=io.StringIO)
class GrepTest(unittest.TestCase):
    # Test grepping a single file
    def test_one_file_one_match_no_flags(self, mock_file, mock_open):
        self.assertMultiLineEqual(
            grep("Agamemnon", "", ["iliad.txt"]), "Of Atreus, Agamemnon, King of men.\n"
        )


if __name__ == "__main__":
    unittest.main()
