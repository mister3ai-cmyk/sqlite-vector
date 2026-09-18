"""
NGP 4.5 Auto-Research Cycle
Harvest → ISO-RAG Filter → Dynamic Test Generation → pytest
"""
import asyncio
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ngp45_engine.research.harvester import AsyncPaperHarvester
from ngp45_engine.research.filter import TopologicalFilterScorer
from ngp45_engine.research.runner import DynamicTestRunner

VECTORS = [
    {
        "name": "Vector 1 — CISS & Tryptophan",
        "keywords": [
            "chiral induced spin selectivity",
            "tryptophan superradiance",
            "non-Hermitian exceptional points",
            "Zak phase photonic",
        ],
        "categories": ["physics.bio-ph", "quant-ph", "physics.optics"],
        "max_results": 8,
    },
    {
        "name": "Vector 2 — D(0) & Rydberg",
        "keywords": [
            "ultradense deuterium",
            "Rydberg matter",
            "Leif Holmlid",
            "phonon-nuclear coupling",
        ],
        "categories": ["physics.atom-ph", "nucl-th", "cond-mat.other"],
        "max_results": 8,
    },
    {
        "name": "Vector 3 — Epigenetics & Nanopore",
        "keywords": [
            "Oxford Nanopore direct methylation",
            "5mC single-cell",
            "DunedinPACE epigenetic clock",
        ],
        "categories": ["q-bio.GN", "q-bio.BM"],
        "max_results": 8,
    },
    {
        "name": "Vector 4 — Hyperbolic & ISO-RAG",
        "keywords": [
            "Poincare disk embedding",
            "hyperbolic graph RAG",
            "isoperimetric Ricci curvature",
            "accelerated PageRank",
        ],
        "categories": ["cs.LG", "math.CO", "cs.IR"],
        "max_results": 8,
    },
]

# ISO-RAG ceiling with hash embeddings (norm=0.85) is ~0.433.
# Set threshold just below that so all topologically-valid papers pass,
# then re-rank by keyword relevance for meaningful ordering.
# TODO: replace _text_to_embedding with sentence-transformers to unlock 0.75+.
MIN_NOVELTY_SCORE = 0.40


async def harvest_vector(harvester: AsyncPaperHarvester, vector: dict) -> list:
    tasks = []
    for kw in vector["keywords"]:
        tasks.append(harvester.fetch_arxiv(kw, vector["max_results"], vector["categories"]))
        tasks.append(harvester.fetch_crossref(kw, vector["max_results"]))
    batches = await asyncio.gather(*tasks)
    papers = []
    for batch in batches:
        for p in batch:
            if not harvester.is_duplicate(p):
                papers.append(p)
    return papers


async def main():
    harvester = AsyncPaperHarvester(rate_limit_delay=0.5)
    scorer = TopologicalFilterScorer(embedding_dim=16, curvature_threshold=0.25)
    runner = DynamicTestRunner()

    total_harvested = 0
    total_passed = 0
    generated_tests = []

    for vec in VECTORS:
        print(f"\n{'='*60}")
        print(f"  {vec['name']}")
        print(f"{'='*60}")

        papers = await harvest_vector(harvester, vec)
        total_harvested += len(papers)
        print(f"  Собрано: {len(papers)} уникальных препринтов")

        scored = scorer.evaluate_and_filter(papers, min_novelty_score=MIN_NOVELTY_SCORE)
        # Re-rank by keyword hit count (semantic boost on top of topological score)
        kw_lower = [k.lower() for k in vec["keywords"]]
        def kw_hits(doc):
            text = f"{doc.get('title','')} {doc.get('abstract','')}".lower()
            return sum(1 for kw in kw_lower if kw in text)
        scored.sort(key=lambda x: (kw_hits(x[0]), x[1]), reverse=True)

        total_passed += len(scored)
        print(f"  Прошло ISO-RAG (score >= {MIN_NOVELTY_SCORE}): {len(scored)}")

        for doc, score in scored[:5]:
            title = (doc.get("title") or "")[:70]
            doi = doc.get("doi", "")[:35]
            src = doc.get("source", "")
            print(f"    {score:.3f} [{src:8s}] {title}")

        for doc, score in scored:
            abstract = doc.get("abstract", "")
            params = runner.extract_parameters(abstract)
            if params:
                safe_id = (doc.get("doi") or doc.get("title", "unknown"))
                fpath = runner.generate_test_file(safe_id, params)
                generated_tests.append(fpath)

    print(f"\n{'='*60}")
    print(f"  ИТОГО: собрано {total_harvested}, прошло фильтр {total_passed}")
    print(f"  Сгенерировано тестов: {len(generated_tests)}")
    print(f"{'='*60}\n")

    if generated_tests:
        test_dir = runner.output_dir
        print(f"  Запуск pytest {test_dir} ...\n")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"],
            capture_output=False,
        )
        sys.exit(result.returncode)
    else:
        print("  Параметры не извлечены ни из одной статьи — dynamic тесты не созданы.")


if __name__ == "__main__":
    asyncio.run(main())
