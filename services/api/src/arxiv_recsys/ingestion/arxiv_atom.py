from datetime import datetime
from xml.etree import ElementTree

from arxiv_recsys.models import Paper
from arxiv_recsys.normalization import canonicalize_paper

ATOM = "http://www.w3.org/2005/Atom"
ARXIV = "http://arxiv.org/schemas/atom"


def _text(element: ElementTree.Element, path: str, default: str = "") -> str:
    value = element.findtext(path, default=default)
    return value.strip() if value else default


def parse_arxiv_atom(payload: str) -> list[Paper]:
    root = ElementTree.fromstring(payload)
    papers: list[Paper] = []

    for entry in root.findall(f"{{{ATOM}}}entry"):
        categories = [
            category.attrib["term"]
            for category in entry.findall(f"{{{ATOM}}}category")
            if category.attrib.get("term")
        ]
        authors = [
            _text(author, f"{{{ATOM}}}name")
            for author in entry.findall(f"{{{ATOM}}}author")
        ]
        primary = entry.find(f"{{{ARXIV}}}primary_category")
        primary_category = (
            primary.attrib.get("term", categories[0] if categories else "")
            if primary is not None
            else categories[0]
        )

        papers.append(
            canonicalize_paper(
                identifier=_text(entry, f"{{{ATOM}}}id"),
                title=_text(entry, f"{{{ATOM}}}title"),
                abstract=_text(entry, f"{{{ATOM}}}summary"),
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published_at=datetime.fromisoformat(
                    _text(entry, f"{{{ATOM}}}published").replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    _text(entry, f"{{{ATOM}}}updated").replace("Z", "+00:00")
                ),
                doi=_text(entry, f"{{{ARXIV}}}doi") or None,
                journal_reference=_text(entry, f"{{{ARXIV}}}journal_ref") or None,
            )
        )

    return papers
