import asyncio
import os
import unittest
import numpy as np

from ngp45_engine.research.harvester import AsyncPaperHarvester
from ngp45_engine.research.filter import TopologicalFilterScorer
from ngp45_engine.research.runner import DynamicTestRunner


class TestAutoResearchHarness(unittest.TestCase):
    def test_harvester_async_fetching_and_deduplication(self):
        harvester = AsyncPaperHarvester(rate_limit_delay=0.01)

        p1 = {"doi": "10.1000/182", "title": "Quantum Biology in Tryptophan"}
        p2 = {"doi": "10.1000/182", "title": "Duplicate DOI Paper"}
        p3 = {"doi": "10.1000/183", "title": "Quantum Biology in Tryptophan"}

        self.assertFalse(harvester.is_duplicate(p1))
        self.assertTrue(harvester.is_duplicate(p2))
        self.assertTrue(harvester.is_duplicate(p3))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        papers = loop.run_until_complete(harvester.harvest_all(["bio-photons"]))
        loop.close()

        self.assertGreater(len(papers), 0, "Harvester should return papers for query mask")
        self.assertIn("title", papers[0])
        self.assertIn("doi", papers[0])

    def test_topological_filter_and_scoring(self):
        scorer = TopologicalFilterScorer(embedding_dim=16, curvature_threshold=0.25)

        docs = [
            {"title": "Rydberg Matter and Holmlid Screening", "abstract": "Quantum physics of ultra-dense deuterium D(0)."},
            {"title": "Irrelevant Recipe for Soup", "abstract": "Boil water and add carrots for lunch."},
            {"title": "Non-Hermitian Tryptophan Superradiance", "abstract": "Lindblad open quantum master equation with gamma_0=0.00273."},
        ]

        scored_docs = scorer.evaluate_and_filter(docs, min_novelty_score=0.1)
        self.assertGreater(len(scored_docs), 0, "Filter should retain relevant domain documents")

        top_doc, top_score = scored_docs[0]
        self.assertGreater(top_score, 0.2, "Top ranked paper should have high novelty score")

    def test_dynamic_runner_parameter_extraction_and_test_generation(self):
        runner = DynamicTestRunner()
        abstract_text = (
            "Observed superradiance mode retention at sigma=0.05 eV with ST efficiency "
            "kappa=16.6 ps^-1 and gamma_0=0.00273 eV. Intercept=51.024577."
        )

        params = runner.extract_parameters(abstract_text)
        self.assertIn("kappa", params)
        self.assertIn("sigma", params)
        self.assertIn("gamma_0", params)
        self.assertIn("dunedin_intercept", params)
        self.assertEqual(params["kappa"], 16.6)
        self.assertEqual(params["dunedin_intercept"], 51.024577)

        test_filepath = runner.generate_test_file("paper_101", params)
        self.assertTrue(os.path.exists(test_filepath), "Generated test file must exist on disk")

        success = runner.run_generated_test(test_filepath)
        self.assertTrue(success, "Generated dynamic test suite must pass cleanly")


if __name__ == "__main__":
    unittest.main()
