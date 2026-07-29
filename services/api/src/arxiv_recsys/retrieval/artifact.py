import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class IndexArtifactManifest(BaseModel):
    schema_version: int = 1
    id: str
    created_at: datetime
    corpus_manifest: str
    encoder: str
    dimensions: int = Field(ge=1)
    vector_count: int = Field(ge=0)
    index_kind: str
    code_revision: str
    files: dict[str, str]

    def write(self, directory: Path) -> Path:
        path = directory / "manifest.json"
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
        )
        return path


def create_manifest(
    *,
    directory: Path,
    artifact_id: str,
    corpus_manifest: str,
    encoder: str,
    dimensions: int,
    vector_count: int,
    index_kind: str,
    code_revision: str,
) -> IndexArtifactManifest:
    files = {
        path.name: sha256_file(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and path.name != "manifest.json"
    }
    return IndexArtifactManifest(
        id=artifact_id,
        created_at=datetime.now(tz=UTC),
        corpus_manifest=corpus_manifest,
        encoder=encoder,
        dimensions=dimensions,
        vector_count=vector_count,
        index_kind=index_kind,
        code_revision=code_revision,
        files=files,
    )


def validate_artifact(directory: Path) -> IndexArtifactManifest:
    manifest = IndexArtifactManifest.model_validate_json(
        (directory / "manifest.json").read_text()
    )
    for filename, expected in manifest.files.items():
        actual = sha256_file(directory / filename)
        if actual != expected:
            raise ValueError(f"Artifact checksum mismatch: {filename}")
    return manifest
