import numpy as np


def summarize(values: list[float]) -> dict:
    if not values:
        raise ValueError("Cannot summarize an empty list")

    data = np.asarray(values, dtype=float)

    return {
        "mean_ms": float(np.mean(data)),
        "median_ms": float(np.median(data)),
        "p95_ms": float(np.percentile(data, 95)),
        "std_ms": float(np.std(data)),
        "min_ms": float(np.min(data)),
        "max_ms": float(np.max(data)),
    }