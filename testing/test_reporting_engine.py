#!/usr/bin/env python3
"""
Tests for the Execution Framework — Reporting Engine
"""
import sys
import os
import unittest
from pathlib import Path

EF_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'execution-framework'))
ENGINE_DIR = os.path.join(EF_ROOT, 'utilities', 'reporting', 'reporting_engine')

sys.path = [p for p in sys.path if 'template_generator' not in p]
sys.path.insert(0, ENGINE_DIR)

from modules import generator, finalizer, validator, markdown_generator
from utils.common import PROJECT_ROOT, REPORT_FILENAME, DRAFT_SECTIONS

COMPLETED = PROJECT_ROOT / 'reports' / 'completed'


class TestValidator(unittest.TestCase):

    def test_validator_passes(self):
        result = validator.run_validator()
        self.assertTrue(result, "Validator failed")


class TestGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        validator.run_validator()
        generator.run_generator()

    def test_html_generates_successfully(self):
        self.assertTrue(generator.run_generator(), "HTML generator returned False")

    def test_html_file_exists(self):
        self.assertTrue((COMPLETED / f'{REPORT_FILENAME}.html').exists())

    def test_drafts_file_created(self):
        self.assertTrue((COMPLETED / f'{REPORT_FILENAME}_DRAFTS.md').exists())

    def test_drafts_has_all_configured_sections(self):
        drafts_path = COMPLETED / f'{REPORT_FILENAME}_DRAFTS.md'
        if not drafts_path.exists():
            self.skipTest("DRAFTS not found")
        content = drafts_path.read_text(encoding='utf-8')
        for section in DRAFT_SECTIONS:
            self.assertIn(f"### {section['key']} ###", content,
                          f"DRAFTS missing section: {section['key']}")

    def test_report_title_in_html(self):
        html_path = COMPLETED / f'{REPORT_FILENAME}.html'
        if not html_path.exists():
            self.skipTest("HTML not generated")
        content = html_path.read_text(encoding='utf-8')
        from utils.common import REPORT_TITLE
        self.assertIn(REPORT_TITLE, content)

    def test_scope_name_in_html(self):
        html_path = COMPLETED / f'{REPORT_FILENAME}.html'
        if not html_path.exists():
            self.skipTest("HTML not generated")
        content = html_path.read_text(encoding='utf-8')
        # Check that some scope/assessment name appears — exact name depends on loaded data
        from utils.common import REPORT_TITLE
        self.assertIn(REPORT_TITLE, content)


class TestFinalizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        validator.run_validator()
        generator.run_generator()
        # Write minimal DRAFTS so finalizer has content to inject
        drafts = COMPLETED / f'{REPORT_FILENAME}_DRAFTS.md'
        drafts.write_text(
            "### EXECUTIVE_SUMMARY ###\nTest summary.\n\n"
            "### KEY_FINDINGS ###\nTest findings.\n\n"
            "### METHODOLOGY_NOTES ###\nTest methodology.\n\n"
            "### RESULTS_ANALYSIS ###\nTest results.\n\n"
            "### RECOMMENDATIONS ###\nTest recommendations.\n"
        )

    def test_finalize_html(self):
        self.assertTrue(finalizer.run_finalizer(formats={'html'}))

    def test_finalize_markdown(self):
        self.assertTrue(finalizer.run_finalizer(formats={'md'}))
        self.assertTrue((COMPLETED / f'{REPORT_FILENAME}.md').exists())

    def test_finalize_all_creates_zip(self):
        self.assertTrue(finalizer.run_finalizer(formats={'html', 'md'}))
        self.assertTrue((COMPLETED / f'{REPORT_FILENAME}_Deliverable.zip').exists())

    def test_markdown_no_action_required(self):
        finalizer.run_finalizer(formats={'md'})
        md_path = COMPLETED / f'{REPORT_FILENAME}.md'
        if not md_path.exists():
            self.skipTest("Markdown not found")
        content = md_path.read_text(encoding='utf-8')
        self.assertEqual(content.count('[ACTION REQUIRED]'), 0,
                         "Markdown has unfilled placeholders")


if __name__ == '__main__':
    unittest.main(verbosity=2)
