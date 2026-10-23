from collections import Counter


def remove_repeated_headers(pages: list[dict], min_pages: int = 3, share: float = 0.5) -> list[dict]:
    """Remove a first/last line that repeats on many pages (a header or footer).

    Example: "Published as a conference paper at ICLR 2024" on every page.
    A line counts as a header/footer if it appears on at least `min_pages`
    pages AND on at least `share` (50%) of all pages.
    """
    if len(pages) < min_pages:
        return pages

    first_lines = Counter()
    last_lines = Counter()
    for p in pages:
        lines = [ln.strip() for ln in p["text"].split("\n") if ln.strip()]
        if lines:
            first_lines[lines[0]] += 1
            last_lines[lines[-1]] += 1

    needed = max(min_pages, share * len(pages))
    bad_first = {line for line, n in first_lines.items() if n >= needed}
    bad_last = {line for line, n in last_lines.items() if n >= needed}

    cleaned = []
    for p in pages:
        lines = [ln for ln in p["text"].split("\n") if ln.strip()]
        if lines and lines[0].strip() in bad_first:
            lines = lines[1:]
        if lines and lines[-1].strip() in bad_last:
            lines = lines[:-1]
        # a last line that is only a page number, like "12"
        if lines and lines[-1].strip().isdigit():
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text:
            cleaned.append({**p, "text": text})
    return cleaned


def is_mostly_numbers(text: str, threshold: float = 0.5) -> bool:
    """True if more than `threshold` of the characters are digits, spaces or symbols.

    This catches tables that PDF extraction turned into a column of numbers.
    """
    if not text:
        return True
    useless = sum(1 for ch in text if not ch.isalpha())
    return useless / len(text) > threshold