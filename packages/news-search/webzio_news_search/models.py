from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Article:
    article_id: str
    url: str
    title: str
    published_at: str
    summary: str = ""
    main_image: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Article:
        data = data or {}
        return cls(
            article_id=str(data.get("article_id") or ""),
            url=str(data.get("url") or ""),
            title=str(data.get("title") or ""),
            published_at=str(data.get("published_at") or ""),
            summary=str(data.get("summary") or ""),
            main_image=str(data.get("main_image") or ""),
        )


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    chunk_index: int | None
    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Chunk:
        data = data or {}
        index = data.get("chunk_index")
        return cls(
            chunk_id=str(data.get("chunk_id") or ""),
            chunk_index=int(index) if isinstance(index, int) else None,
            text=str(data.get("text") or ""),
        )


@dataclass(frozen=True)
class NewsResult:
    score: float
    article: Article
    chunk: Chunk
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NewsResult:
        score = data.get("score")
        return cls(
            score=float(score) if isinstance(score, (int, float)) else 0.0,
            article=Article.from_dict(data.get("article")),
            chunk=Chunk.from_dict(data.get("chunk")),
            metadata=dict(data.get("metadata") or {}),
            raw=data,
        )

    @property
    def title(self) -> str:
        return self.article.title

    @property
    def url(self) -> str:
        return self.article.url

    @property
    def text(self) -> str:
        return self.chunk.text

    @property
    def domain(self) -> str:
        return str(self.metadata.get("domain") or "")

    def to_text(self, index: int | None = None) -> str:
        """renders one result as a compact block for prompts and logs."""
        head = self.article.title or self.article.url or "(untitled)"
        if index is not None:
            head = f"{index}. {head}"
        lines = [head]
        if self.article.url:
            lines.append(f"   URL: {self.article.url}")
        if self.article.published_at:
            lines.append(f"   Published: {self.article.published_at}")
        lines.append(f"   Score: {self.score:g}")
        source_bits = [
            str(self.metadata[key])
            for key in ("domain", "country", "language")
            if self.metadata.get(key)
        ]
        if source_bits:
            lines.append(f"   Source: {' | '.join(source_bits)}")
        for key in ("sentiment", "political_bias", "trust_category"):
            if self.metadata.get(key):
                lines.append(f"   {key.replace('_', ' ').title()}: {self.metadata[key]}")
        for key in ("ticker", "organization", "person", "location", "topic"):
            values = self.metadata.get(key)
            if values:
                joined = ", ".join(str(item) for item in values) if isinstance(values, list) else str(values)
                lines.append(f"   {key.title()}: {joined}")
        if self.chunk.text:
            lines.append(f"   Excerpt: {self.chunk.text.strip()}")
        return "\n".join(lines)


@dataclass(frozen=True)
class NewsSearchResponse:
    query: str
    total_results: int
    results: list[NewsResult]
    requests_left: int | None = None
    credits_used: int | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any], query: str = "") -> NewsSearchResponse:
        items = data.get("results") or []
        results = [NewsResult.from_dict(item) for item in items if isinstance(item, dict)]
        total = data.get("total_results")
        return cls(
            query=str(data.get("query") or query),
            total_results=int(total) if isinstance(total, int) else len(results),
            results=results,
            requests_left=_optional_int(data.get("requests_left")),
            credits_used=_optional_int(data.get("credits_used")),
            raw=data,
        )

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def to_text(self) -> str:
        """renders the whole response as prompt-friendly text."""
        header = [f"Query: {self.query}", f"Results: {len(self.results)}"]
        if not self.results:
            return "\n".join(header + ["No matching articles."])
        blocks = [result.to_text(index) for index, result in enumerate(self.results, start=1)]
        return "\n".join(header) + "\n\n" + "\n\n".join(blocks)

    def to_dicts(self) -> list[dict[str, Any]]:
        """flat rows: one dict per result, handy for sheets and dataframes."""
        rows: list[dict[str, Any]] = []
        for result in self.results:
            rows.append(
                {
                    "score": result.score,
                    "title": result.article.title,
                    "url": result.article.url,
                    "published_at": result.article.published_at,
                    "summary": result.article.summary,
                    "excerpt": result.chunk.text,
                    **{f"metadata_{key}": value for key, value in result.metadata.items()},
                }
            )
        return rows


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
