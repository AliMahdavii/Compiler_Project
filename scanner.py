"""Phase 1 scanner (lexical analyzer), written by hand.

The DFA table is read from transition_table.csv when the program runs.
We don't use if/else to decide the states. We just look up the next state in the table:

    next_state = table[(state, character_class)]
"""

import csv
import string
import sys
from dataclasses import dataclass
from pathlib import Path

# keywords look like normal identifiers, so we check this dict after scanning a word
KEYWORDS = {"int": "KEYWORD_INT", "if": "KEYWORD_IF"}
# q0 = start state, dead = "no way to continue", SKIP = throw this lexeme away (whitespace)
START, DEAD, SKIP = "q0", "dead", "SKIP"

# every character has a class (a column in the csv). Anything not listed here is "other"
CHAR_CLASS = {
    **{c: "letter" for c in string.ascii_letters + "_"},
    **{c: "digit" for c in string.digits},
    **{c: c for c in "+=()"},
    **{c: "whitespace" for c in " \t\r\n"},
}


# one token: its kind, the text, and where it is in the code
@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    line: int
    column: int


# one lexical error: where it is and which character caused it
@dataclass(frozen=True)
class LexError:
    line: int
    column: int
    char: str

    def __str__(self):
        return f"Lexical error at line {self.line}, column {self.column}: invalid character {self.char!r}"


class Scanner:
    def __init__(self, table_path):
        with open(table_path, newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            self.header = reader.fieldnames          # first = state, last = token, the middle ones = character classes
            self.rows = list(reader)
        classes = self.header[1:-1]
        self.table = {(row["state"], c): row[c] for row in self.rows for c in classes}
        self.accepts = {row["state"]: row["token"] for row in self.rows}   # which token each accepting state gives

    def scan(self, source):
        """Go through the source code and return (tokens, errors). It keeps going after an error."""
        tokens, errors = [], []
        pos, line, column = 0, 1, 1
        while pos < len(source):
            # start from q0 and keep moving while the table has a next state (so we get the longest match)
            state, end = START, pos
            while end < len(source):
                next_state = self.table.get((state, CHAR_CLASS.get(source[end], "other")), DEAD)
                if next_state == DEAD:
                    break
                state, end = next_state, end + 1

            if end == pos:                                   # we did not move at all, so this character is illegal
                errors.append(LexError(line, column, source[pos]))
                end = pos + 1
            elif self.accepts[state] != SKIP:                # whitespace is not a token
                lexeme = source[pos:end]
                # if the word is a keyword (int, if) use the keyword kind, otherwise use the kind from the table
                tokens.append(Token(KEYWORDS.get(lexeme, self.accepts[state]), lexeme, line, column))

            line, column = self._advance(source[pos:end], line, column)
            pos = end
        return tokens, errors

    @staticmethod
    def _advance(text, line, column):
        # move line and column forward over the text we just read
        for char in text:
            line, column = (line + 1, 1) if char == "\n" else (line, column + 1)
        return line, column


def main():
    base = Path(__file__).parent
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "samples" / "valid.ns"
    tokens, errors = Scanner(base / "transition_table.csv").scan(path.read_text(encoding="utf-8"))
    print(f"{'KIND':<14}{'LEXEME':<12}{'LINE':<6}COLUMN")
    for t in tokens:
        print(f"{t.kind:<14}{t.lexeme:<12}{t.line:<6}{t.column}")
    print()
    print("\n".join(map(str, errors)) if errors else "No lexical errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
