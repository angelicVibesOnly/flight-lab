# AI Usage Disclosure

## Tools used

- Claude (Anthropic), model Claude Opus 5.5, used through claude.ai
- [Add any other AI tools you used for this lab, or delete this line]

## Conversation links

- Link 1: [paste the share link to the Claude chat from 24 Nov 2026]
- Link 2: [add a link for any other AI conversation about this lab, or delete this line]

## What I used them for

- Explaining Python regular expressions: the `re` module, `match` vs `fullmatch`, and why `\d`, `isalnum()` and `isupper()` accept non-ASCII characters such as `Ā` or full-width `１`
- Explaining `\r\n` line endings, relative paths (`db.csv` vs `data/db.csv`) and why `YYYY-MM-DD HH:MM` strings can be compared directly
- Explaining how the logging handler is removed after each run
- Fixing a rejected `git push` to my GitHub repository
- Debugging `flight_parser.py`
- Planning and writing `query.py`
- Planning `validator.py` around a shared `parse_datetime` function
- Reviewing and testing my versions of `query.py` and `validator.py`
- Generating test scripts with edge cases

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| `query.py` | Whole module: query validation, filtering, sorting, `limit`, `run_query`, `run_queries` | Claude generated a full first version. I adapted it (helper names, importing `parse_datetime` from `validator.py`, tuples for the key lists). Claude then reviewed and tested my version. |
| `validator.py` | `parse_datetime` | Code provided by Claude (regex with `[0-9]` plus `strptime`, no stripping, returns `None` for non-strings) |
| `validator.py` | `validate_row`, `to_record`, `load_airports` | Claude explained the structure: check order, ASCII-only regexes, price checks with `math.isfinite`, stripping in `validate_row`. It also gave a skeleton for checks 1–3, then reviewed and tested the final file. |
| `flight_parser.py` | `answer_queries`, `build_database`, `build_parser`, `write_log` | Modified: Claude found and fixed a missing colon (`except OSError as exc:`), the `recrds`/`records` typo and the `prog` name typo, and added `logger.propagate = False` |

## Key prompts

1. "I don't understand how I should go about doing query", with the full assignment description pasted in.
2. "Can you tell me how I should work on validator considering my query?"
3. "Can you check what's wrong here?", with my `flight_parser.py` pasted in.

## What I changed or verified myself
I adapted the generated `query.py` (helper names, tuples, shared `parse_datetime` import) and wrote the complete `validate_row`, `to_record` and `load_airports` myself from the plan. I ran both check scripts after every change, fixed the edge cases they surfaced, confirmed the order-without-sort_by and string-datetime rules against the spec, and verified the public tests once `csv_loader.py` was finished.


