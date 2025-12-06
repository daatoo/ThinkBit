## `src/aegisai/moderation` – Text / transcript profanity moderation

This package provides **shared profanity vocabulary**, **text analysis rules**, and a simple **policy hook** used by both text and audio (STT) sides of Aegis.

Files:

- `bad_words_list.py`
- `policy.py`
- `text_rules.py`

---

### `bad_words_list.py`

Shared profanity list + normalization / matching helpers.

- `BAD_WORDS: set[str]`
  - Includes:
    - Core profanity (`fuck`, `shit`, `bitch`, `asshole`, `bastard`, `cunt`, `dick`, `piss`, `damn`, `crap`, `hell`, …)
    - Soft profanity / rhetoric (`frick`, `freaking`, `dang`, `heck`, `wtf`, `omfg`, …)
    - Extended sexual profanity and compound insults (`cock`, `ballsack`, `shithead`, `scumbag`, `asswipe`, `fucknugget`, …)
    - Abusive non-hate insults (`idiot`, `moron`, `stupid`, `loser`, `trash`, …)
    - Aggressive phrases and self-harm–like commands (`kill yourself`, `kys`, `go die`, `shut the fuck up`, `fuck you`, …)
    - Common misspellings / obfuscated forms (`fuk`, `fck`, `sh1t`, `b1tch`, `c0ck`, `cr@p`, …)
    - Sexualized insult terms (`slut`, `whore`, `hoe`, …)
    - Threat-like lines (`i'll beat your ass`, `break your face`, …)
    - Highly abusive “waste of space / garbage human” style phrases, etc.
  - The set currently also contains some harmless words (e.g. `"today"`, `"english"`, etc.) for testing / demo purposes.

- `_WORD_RE = re.compile(r"[^a-z0-9]+")`
  - Used for normalization (strip everything except lowercase letters and digits).

- `normalize_text_for_matching(text: str) -> str`
  - Lowercases the text.
  - Replaces any non `[a-z0-9]` character with a space.
  - Used for whole-phrase search (e.g. multi-word entries like `"son of a bitch"`).

- `normalize_token(token: str) -> str`
  - Lowercases and strips all non `[a-z0-9]`.
  - Used for single-token comparison.

- `is_bad_word(token: str, extra_bad: Iterable[str] | None = None) -> bool`
  - Normalizes `token` and checks membership in:
    - `BAD_WORDS` by default, or
    - `BAD_WORDS ∪ set(extra_bad)` if `extra_bad` provided.
  - Intended for **word-level** checks (e.g. audio STT tokens).

- `find_bad_words_in_text(text: str) -> list[str]`
  - Normalizes the entire string with `normalize_text_for_matching`.
  - For each entry `w` in `BAD_WORDS`, builds a whole-word regex:
    ```python
    r"\b" + re.escape(w) + r"\b"
    ```
  - Adds `w` to the result list if the pattern matches.
  - This is the main function used by the text rules.

---

### `text_rules.py`

Rules for analyzing text or transcripts using the shared profanity list.

- `@dataclass TextModerationResult`
  - `original_text: str` – the full text that was analyzed.
  - `bad_words: list[str]` – all matched entries from `BAD_WORDS`.
  - `count: int` – length of `bad_words`.
  - `severity: int` – coarse severity bucket (0–3).
  - `block: bool` – final decision from the text rules.

- `_compute_severity(count: int) -> int`
  - Simple mapping:
    - `0` bad words → severity `0` (clean)
    - `1–2` bad words → severity `1` (mild)
    - `3–4` bad words → severity `2` (strong)
    - `5+` bad words → severity `3` (extreme)

- `analyze_text(text: str) -> TextModerationResult`
  - Uses `find_bad_words_in_text(text)` to get `found`.
  - `count = len(found)`.
  - `severity = _compute_severity(count)`.
  - **Blocking rule (local to text_rules):**
    ```python
    block = severity >= 2  # i.e. 3+ bad words
    ```
  - Returns a fully populated `TextModerationResult`.

- `analyze_transcript(chunks: list[str]) -> TextModerationResult`
  - Joins all chunks with spaces: `" ".join(chunks)`.
  - Delegates to `analyze_text(joined)`.
  - Useful for whole-audio transcripts or multi-line inputs.

---

### `policy.py`

Very small policy hook that can be extended with modes in the future.

- Imports `TextModerationResult` from `text_rules`.

- `should_block_text(result: TextModerationResult, mode: str = "default") -> bool`
  - Current logic:
    ```python
    return result.count > 0
    ```
  - i.e. **policy** is stricter than `text_rules`’ local `block` flag:
    - `analyze_text` only sets `block=True` for severity ≥ 2 (3+ bad words),
    - `should_block_text` says “block whenever `count > 0`”.
  - The `mode` parameter is reserved for future variations (child/teen/adult/streamer/custom, etc.).

---
