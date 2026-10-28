"""Run with:  python -m unittest -v"""
import csv
import tempfile
import unittest
from pathlib import Path

from scanner import Scanner

BASE = Path(__file__).parent
scanner = Scanner(BASE / "transition_table.csv")


def kinds(source):
    return [(t.kind, t.lexeme) for t in scanner.scan(source)[0]]


class ScannerTests(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(kinds("int if"), [("KEYWORD_INT", "int"), ("KEYWORD_IF", "if")])

    def test_keyword_look_alikes_are_identifiers(self):
        for word in ("integer", "iff", "i", "in", "_if"):
            self.assertEqual(kinds(word), [("IDENTIFIER", word)])

    def test_identifier_integer_symbols(self):
        self.assertEqual(kinds("a1 + 42 = (b)"),
                         [("IDENTIFIER", "a1"), ("PLUS", "+"), ("INTEGER", "42"), ("EQUAL", "="),
                          ("LPAREN", "("), ("IDENTIFIER", "b"), ("RPAREN", ")")])

    def test_no_spaces_needed(self):
        self.assertEqual([l for _, l in kinds("x=y+12")], ["x", "=", "y", "+", "12"])

    def test_whitespace_is_dropped(self):
        self.assertEqual(kinds(" \t\n\r\n "), [])
        self.assertEqual(kinds(""), [])

    def test_line_and_column(self):
        tokens, _ = scanner.scan("int x\n  y = 2")
        self.assertEqual([(t.lexeme, t.line, t.column) for t in tokens],
                         [("int", 1, 1), ("x", 1, 5), ("y", 2, 3), ("=", 2, 5), ("2", 2, 7)])

    def test_illegal_character_is_reported_and_scanning_continues(self):
        tokens, errors = scanner.scan("a @ b\n$ c")
        self.assertEqual([t.lexeme for t in tokens], ["a", "b", "c"])
        self.assertEqual([(e.char, e.line, e.column) for e in errors], [("@", 1, 3), ("$", 2, 1)])

    def test_illegal_character_glued_to_tokens(self):
        tokens, errors = scanner.scan("ab@12")
        self.assertEqual([t.lexeme for t in tokens], ["ab", "12"])
        self.assertEqual(len(errors), 1)

    def test_only_english_letters_and_digits(self):
        _, errors = scanner.scan("é ۱ ²")
        self.assertEqual([e.char for e in errors], ["é", "۱", "²"])

    def test_number_followed_by_letters_is_two_tokens(self):
        self.assertEqual(kinds("12abc"), [("INTEGER", "12"), ("IDENTIFIER", "abc")])

    def test_always_terminates(self):
        _, errors = scanner.scan("".join(chr(i) for i in range(1, 700)))
        self.assertTrue(errors)

    def test_table_really_drives_the_scanner(self):
        """Changing the CSV (state q3: PLUS -> ADD) changes the output; no code change."""
        with open(BASE / "transition_table.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        for row in rows:
            row[-1] = "ADD" if row[0] == "q3" else row[-1]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "table.csv"
            path.write_text("\n".join(",".join(r) for r in rows), encoding="utf-8")
            self.assertEqual(Scanner(path).scan("+")[0][0].kind, "ADD")

    def test_sample_files(self):
        expected_errors = {"valid.ns": 0, "arithmetic.ns": 0, "identifiers.ns": 0,
                           "invalid.ns": 1, "errors.ns": 2}
        for name, count in expected_errors.items():
            _, errors = scanner.scan((BASE / "samples" / name).read_text(encoding="utf-8"))
            self.assertEqual(len(errors), count, name)


if __name__ == "__main__":
    unittest.main()
