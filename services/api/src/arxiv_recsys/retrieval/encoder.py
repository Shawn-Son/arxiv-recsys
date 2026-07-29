import hashlib
import re
from itertools import pairwise

import numpy as np
from numpy.typing import NDArray

TOKEN_PATTERN = re.compile(r"\w+")


class HashingTextEncoder:
    """Deterministic offline baseline with the production encoder contract.

    This is intentionally labeled as a baseline. Full-corpus releases replace it
    with a versioned scientific sentence encoder while retaining the same index
    and artifact interfaces.
    """

    name = "hashing-baseline-v1"

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions < 32:
            raise ValueError("Encoder dimensions must be at least 32")
        self.dimensions = dimensions

    def encode(self, texts: list[str]) -> NDArray[np.float32]:
        matrix = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = TOKEN_PATTERN.findall(text.casefold())
            features = tokens + [f"{left}_{right}" for left, right in pairwise(tokens)]
            for feature in features:
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, byteorder="big")
                column = value % self.dimensions
                sign = 1.0 if value & 1 else -1.0
                matrix[row, column] += sign

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return matrix / norms
