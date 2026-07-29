import argparse
import json
import shutil
from pathlib import Path

from arxiv_recsys.models import Paper
from arxiv_recsys.repository import FixturePaperRepository
from arxiv_recsys.retrieval.artifact import create_manifest, validate_artifact
from arxiv_recsys.retrieval.encoder import HashingTextEncoder
from arxiv_recsys.retrieval.vector_index import FaissVectorIndex


def read_jsonl(path: Path) -> list[Paper]:
    return [
        Paper.model_validate(json.loads(line))
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an immutable FAISS artifact from canonical paper records."
    )
    parser.add_argument("--input-jsonl", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--corpus-manifest", required=True)
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--dimensions", type=int, default=384)
    arguments = parser.parse_args()

    papers = (
        read_jsonl(arguments.input_jsonl)
        if arguments.input_jsonl
        else list(FixturePaperRepository.from_package_data().all())
    )
    if arguments.output.exists():
        raise SystemExit(f"Refusing to overwrite existing artifact: {arguments.output}")

    staging = arguments.output.with_name(f".{arguments.output.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    encoder = HashingTextEncoder(dimensions=arguments.dimensions)
    documents = [f"{paper.title} {paper.abstract}" for paper in papers]
    index = FaissVectorIndex(dimensions=encoder.dimensions)
    index.add([paper.arxiv_id for paper in papers], encoder.encode(documents))
    index.save(staging)

    manifest = create_manifest(
        directory=staging,
        artifact_id=arguments.artifact_id,
        corpus_manifest=arguments.corpus_manifest,
        encoder=encoder.name,
        dimensions=encoder.dimensions,
        vector_count=len(papers),
        index_kind="faiss-hnsw",
        code_revision=arguments.code_revision,
    )
    manifest.write(staging)
    validate_artifact(staging)
    staging.rename(arguments.output)
    print(arguments.output / "manifest.json")


if __name__ == "__main__":
    main()
