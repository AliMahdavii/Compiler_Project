"""Phase 1: manual, table-driven scanner for the NovaScript+ subset.

All state transitions live in transition_table.csv (loaded at run time).
The scanner never decides transitions with if/else; it only looks them up:

    next_state = table[(state, character_class)]
"""

import csv
import string
import sys
from dataclasses import dataclass
from pathlib import Path

KEYWORDS = {"int": "KEYWORD_INT", "if": "KEYWORD_IF"}
START, DEAD, SKIP = "q0", "dead", "SKIP"   # start state, "no transition", "ignore this lexeme"

# Character -> column name of the table. Any other character is "other".
CHAR_CLASS = {
    **{c: "letter" for c in string.ascii_letters + "_"},
    **{c: "digit" for c in string.digits},
    **{c: c for c in "+=()"},
    **{c: "whitespace" for c in " \t\r\n"},
}


@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    line: int
    column: int


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
            self.header = reader.fieldnames          # state, <character classes...>, token
            self.rows = list(reader)
        classes = self.header[1:-1]
        self.table = {(row["state"], c): row[c] for row in self.rows for c in classes}
        self.accepts = {row["state"]: row["token"] for row in self.rows}   # state -> token kind

    def scan(self, source):
        """Return (tokens, errors). Scanning continues after every error."""
        tokens, errors = [], []
        pos, line, column = 0, 1, 1
        while pos < len(source):
            # Run the DFA from q0 as far as the table allows (longest match).
            state, end = START, pos
            while end < len(source):
                next_state = self.table.get((state, CHAR_CLASS.get(source[end], "other")), DEAD)
                if next_state == DEAD:
                    break
                state, end = next_state, end + 1

            if end == pos:                                   # q0 has no move: illegal character
                errors.append(LexError(line, column, source[pos]))
                end = pos + 1
            elif self.accepts[state] != SKIP:                # whitespace is dropped
                lexeme = source[pos:end]
                tokens.append(Token(KEYWORDS.get(lexeme, self.accepts[state]), lexeme, line, column))

            line, column = self._advance(source[pos:end], line, column)
            pos = end
        return tokens, errors

    @staticmethod
    def _advance(text, line, column):
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
