"""Stable recursive merge sort with comparison, write, and event counters."""
from typing import Any, Callable


def sort(values: list[Any], key: Callable[[Any], Any] | None = None,
         capture_events: bool = True) -> dict[str, Any]:
    key = key or (lambda x: x)
    data = list(values)
    events, counts = [], {"comparisons": 0, "assignments": 0}

    def merge_sort(lo: int, hi: int) -> None:
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        if capture_events: events.append({"type": "divide", "lo": lo, "mid": mid, "hi": hi})
        merge_sort(lo, mid)
        merge_sort(mid, hi)
        left, right = data[lo:mid], data[mid:hi]
        i = j = 0
        for out in range(lo, hi):
            if i < len(left) and (j >= len(right) or key(left[i]) <= key(right[j])):
                if j < len(right): counts["comparisons"] += 1
                data[out] = left[i]; i += 1
            else:
                counts["comparisons"] += 1
                data[out] = right[j]; j += 1
            counts["assignments"] += 1
        if capture_events: events.append({"type": "merge", "lo": lo, "hi": hi, "values": data[lo:hi]})

    merge_sort(0, len(data))
    return {"sorted": data, **counts, "operations": counts["comparisons"] + counts["assignments"], "events": events}
