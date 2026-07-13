#!/usr/bin/env python3
"""
Tests for the Execution Framework — Template Generator
"""
import sys
import os
import unittest

EF_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'execution-framework'))
TGEN    = os.path.join(EF_ROOT, 'utilities', 'template_generator')
sys.path.insert(0, TGEN)

from core.config import METHODOLOGY_DIR, EXECUTION_TEMPLATES_DIR
from core.parser import parse_methodology
from modules.execution_gen import (
    generate_file_markdown, generate_master_log, analyze_discrepancies
)
from modules.linter import run_linter
from utils.helpers import write_file


class TestTemplateGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.meth_data = parse_methodology(METHODOLOGY_DIR)

    def test_parse_methodology_returns_data(self):
        self.assertTrue(len(self.meth_data) > 0, "parse_methodology returned no phases")

    def test_has_expected_phases(self):
        phase_names = list(self.meth_data.keys())
        self.assertTrue(any('Planning' in p for p in phase_names))
        self.assertTrue(any('Execution' in p for p in phase_names))
        self.assertTrue(any('Delivery' in p for p in phase_names))

    def test_generate_file_markdown_structure(self):
        for phase_folder, files in self.meth_data.items():
            for file_name, categories in files.items():
                if any(len(i) > 0 for i in categories.values()):
                    md = generate_file_markdown(file_name, categories)
                    self.assertIn('## Checklist', md)
                    self.assertIn('## Execution Notes', md)
                    self.assertIn('<a id="cl-', md)
                    return

    def test_generate_master_log_structure(self):
        content = generate_master_log(self.meth_data)
        self.assertIn('# Master Log', content)
        self.assertIn('## Checklist', content)
        self.assertIn('## Execution Notes', content)
        self.assertIn('Phase Notes', content)

    def test_full_rebuild_zero_discrepancies(self):
        write_file(os.path.join(EXECUTION_TEMPLATES_DIR, '00_master_log.md'),
                   generate_master_log(self.meth_data))
        for pf, files in self.meth_data.items():
            for fn, cats in files.items():
                if any(len(i) > 0 for i in cats.values()):
                    write_file(os.path.join(EXECUTION_TEMPLATES_DIR, pf, fn),
                               generate_file_markdown(fn, cats))
        self.assertEqual(len(analyze_discrepancies(self.meth_data, EXECUTION_TEMPLATES_DIR)), 0)

    def test_linter_passes(self):
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            run_linter()
        self.assertIn('LINT PASSED', f.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
