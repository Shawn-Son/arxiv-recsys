"use client";

import { FormEvent, useMemo, useState } from "react";
import { categoryOptions, papers, type Paper } from "../data/papers";

function SearchMark() {
  return <span aria-hidden="true" className="search-mark" />;
}

function BookmarkMark({ saved }: { saved: boolean }) {
  return (
    <span aria-hidden="true" className={`bookmark-mark ${saved ? "is-saved" : ""}`}>
      {saved ? "●" : "○"}
    </span>
  );
}

function PaperCard({
  paper,
  index,
  saved,
  onSave,
  onOpen,
}: {
  paper: Paper;
  index: number;
  saved: boolean;
  onSave: () => void;
  onOpen: () => void;
}) {
  return (
    <article className="paper-card">
      <div className="rank-column" aria-label={`Rank ${index + 1}`}>
        <span>{String(index + 1).padStart(2, "0")}</span>
        <span className="score">{Math.round(paper.score * 100)}</span>
      </div>
      <div className="paper-body">
        <div className="paper-meta">
          <span className="source-pill">{paper.source}</span>
          <span>{paper.published}</span>
          <span>{paper.categories.join(" · ")}</span>
        </div>
        <button className="paper-title-button" onClick={onOpen} type="button">
          <h2>{paper.title}</h2>
        </button>
        <p className="authors">{paper.authors.join(", ")}</p>
        <p className="abstract">{paper.abstract}</p>
        <div className="paper-footer">
          <span className="signal">{paper.signal}</span>
          <div className="paper-actions">
            <span>{paper.citations.toLocaleString()} citations</span>
            <button
              aria-label={`${saved ? "Remove" : "Save"} ${paper.title}`}
              aria-pressed={saved}
              className="save-button"
              onClick={onSave}
              type="button"
            >
              <BookmarkMark saved={saved} />
              {saved ? "Saved" : "Save"}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function PaperDetail({
  paper,
  onClose,
}: {
  paper: Paper;
  onClose: () => void;
}) {
  return (
    <div className="detail-backdrop" role="presentation" onMouseDown={onClose}>
      <article
        aria-labelledby="paper-detail-title"
        aria-modal="true"
        className="detail-panel"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <button aria-label="Close paper details" className="close-button" onClick={onClose}>
          Close
        </button>
        <p className="eyebrow">Paper record · {paper.id}</p>
        <h2 id="paper-detail-title">{paper.title}</h2>
        <p className="detail-authors">{paper.authors.join(", ")}</p>
        <div className="detail-rule" />
        <p className="detail-abstract">{paper.abstract}</p>
        <dl className="detail-grid">
          <div>
            <dt>Published</dt>
            <dd>{paper.published}</dd>
          </div>
          <div>
            <dt>Last revised</dt>
            <dd>{paper.updated}</dd>
          </div>
          <div>
            <dt>Citations</dt>
            <dd>{paper.citations.toLocaleString()}</dd>
          </div>
          <div>
            <dt>Match</dt>
            <dd>{Math.round(paper.score * 100)}%</dd>
          </div>
        </dl>
        <section className="why-panel">
          <p className="eyebrow">Why this surfaced</p>
          <p>{paper.signal}. The title and abstract align with the active research query.</p>
        </section>
        <a
          className="primary-link"
          href={`https://arxiv.org/abs/${paper.id}`}
          rel="noreferrer"
          target="_blank"
        >
          Read on arXiv <span aria-hidden="true">↗</span>
        </a>
      </article>
    </div>
  );
}

export function ResearchWorkspace() {
  const [draftQuery, setDraftQuery] = useState(
    "language models for scientific discovery",
  );
  const [activeQuery, setActiveQuery] = useState(
    "language models for scientific discovery",
  );
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("relevance");
  const [saved, setSaved] = useState<Set<string>>(new Set(["2304.05376"]));
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);

  const rankedPapers = useMemo(() => {
    const terms = activeQuery
      .toLowerCase()
      .split(/\W+/)
      .filter((term) => term.length > 2);

    return papers
      .filter((paper) => category === "all" || paper.categories.includes(category))
      .map((paper) => {
        const haystack = `${paper.title} ${paper.abstract}`.toLowerCase();
        const queryBonus =
          terms.filter((term) => haystack.includes(term)).length * 0.012;
        return { ...paper, displayScore: paper.score + queryBonus };
      })
      .sort((a, b) => {
        if (sort === "newest") {
          return b.published.localeCompare(a.published);
        }
        if (sort === "citations") {
          return b.citations - a.citations;
        }
        return b.displayScore - a.displayScore;
      });
  }, [activeQuery, category, sort]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActiveQuery(draftQuery.trim() || "scientific discovery");
  }

  function toggleSaved(id: string) {
    setSaved((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Aster home">
          <span className="brand-glyph" aria-hidden="true">
            ✦
          </span>
          <span>Aster</span>
        </a>
        <nav aria-label="Primary navigation">
          <a className="active" href="#discover">
            Discover
          </a>
          <a href="#library">Library <sup>{saved.size}</sup></a>
          <a href="#method">Method</a>
        </nav>
        <button className="profile-button" type="button">
          <span className="profile-dot" aria-hidden="true" />
          Research workspace
        </button>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">A citation-aware research engine</p>
          <h1>
            Find the work that
            <br />
            <em>changes your direction.</em>
          </h1>
          <p className="hero-subtitle">
            Search the literature frontier with transparent ranking,
            citation context, and recommendations that learn from your work.
          </p>
        </div>
        <aside className="edition-note" aria-label="Index status">
          <span>Research preview</span>
          <strong>Foundation release</strong>
          <p>Representative records · live ranking interactions</p>
        </aside>
      </section>

      <section className="search-section" id="discover">
        <form className="search-form" onSubmit={submitSearch}>
          <SearchMark />
          <label className="sr-only" htmlFor="research-query">
            Research question
          </label>
          <input
            id="research-query"
            onChange={(event) => setDraftQuery(event.target.value)}
            placeholder="Ask a research question or paste a paper title"
            value={draftQuery}
          />
          <span className="keyboard-hint" aria-hidden="true">⌘ K</span>
          <button type="submit">Search</button>
        </form>
        <div className="search-controls">
          <label>
            <span>Field</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Rank by</span>
            <select value={sort} onChange={(event) => setSort(event.target.value)}>
              <option value="relevance">Relevance</option>
              <option value="newest">Newest first</option>
              <option value="citations">Citation count</option>
            </select>
          </label>
          <p className="result-count">
            {rankedPapers.length} representative results for “{activeQuery}”
          </p>
        </div>
      </section>

      <div className="workspace-layout">
        <section aria-label="Ranked papers" className="results">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Ranked reading list</p>
              <h2>Evidence before popularity</h2>
            </div>
            <p>Dense + lexical retrieval · transparent reranking</p>
          </div>
          {rankedPapers.map((paper, index) => (
            <PaperCard
              index={index}
              key={paper.id}
              onOpen={() => setSelectedPaper(paper)}
              onSave={() => toggleSaved(paper.id)}
              paper={paper}
              saved={saved.has(paper.id)}
            />
          ))}
        </section>

        <aside className="research-sidebar">
          <section className="sidebar-block" id="library">
            <p className="eyebrow">Your library</p>
            <div className="big-number">{saved.size.toString().padStart(2, "0")}</div>
            <h3>papers shaping this trail</h3>
            <p>
              Saves become explicit recommendation signals. You can always see
              why a paper was ranked.
            </p>
          </section>
          <section className="sidebar-block topic-map">
            <div className="sidebar-heading">
              <p className="eyebrow">Reading map</p>
              <span>Last 30 days</span>
            </div>
            <div className="topic-row">
              <span>Scientific agents</span>
              <i style={{ width: "86%" }} />
              <b>42%</b>
            </div>
            <div className="topic-row">
              <span>Evaluation</span>
              <i style={{ width: "62%" }} />
              <b>31%</b>
            </div>
            <div className="topic-row">
              <span>Tool use</span>
              <i style={{ width: "38%" }} />
              <b>18%</b>
            </div>
          </section>
          <section className="sidebar-block daily-brief">
            <span className="brief-index">01</span>
            <div>
              <p className="eyebrow">Daily brief</p>
              <h3>Three new papers overlap your saved research trail.</h3>
              <button type="button">Review the brief <span aria-hidden="true">→</span></button>
            </div>
          </section>
        </aside>
      </div>

      <section className="method-section" id="method">
        <div>
          <p className="eyebrow">The ranking contract</p>
          <h2>Useful systems show their work.</h2>
        </div>
        <ol>
          <li>
            <span>01</span>
            <h3>Retrieve broadly</h3>
            <p>Lexical and semantic indexes find exact language and conceptual neighbors.</p>
          </li>
          <li>
            <span>02</span>
            <h3>Rerank carefully</h3>
            <p>A cross-encoder reads the query and candidates together before ordering results.</p>
          </li>
          <li>
            <span>03</span>
            <h3>Explain the signal</h3>
            <p>Every recommendation names the evidence that placed it in your reading path.</p>
          </li>
        </ol>
      </section>

      <footer>
        <a className="brand footer-brand" href="#top">
          <span className="brand-glyph" aria-hidden="true">✦</span>
          <span>Aster</span>
        </a>
        <p>Open research discovery, engineered for reproducibility.</p>
        <a href="https://github.com/Shawn-Son/arxiv-recsys">Source on GitHub ↗</a>
      </footer>

      {selectedPaper ? (
        <PaperDetail paper={selectedPaper} onClose={() => setSelectedPaper(null)} />
      ) : null}
    </main>
  );
}
