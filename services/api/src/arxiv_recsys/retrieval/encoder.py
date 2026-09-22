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

    name = "hashing-baseline-v2"

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
                # The column and the sign must come from independent halves of
                # the digest. Deriving both from one integer ties the sign to
                # the column parity whenever the dimension count is even, so
                # colliding features always accumulate instead of cancelling.
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
                column = int.from_bytes(digest[:8], byteorder="big") % self.dimensions
                sign = 1.0 if digest[8] & 1 else -1.0
                matrix[row, column] += sign

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return matrix / norms
