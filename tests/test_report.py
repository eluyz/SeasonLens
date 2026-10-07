"""Check exported meaning, missing chart gaps and the local file workflow."""

from datetime import date
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree

import pandas as pd

from seasonlens import analyze_seasonality, render_seasonal_report


def daily(dates, values):
    return pd.DataFrame({'date': pd.to_datetime(dates), 'value': values})


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        if tag in ('th', 'td'):
            self.cell = ''

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.row is not None:
            self.row.append(self.cell)
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


class ReportTests(unittest.TestCase):
    def test_exported_manual_values_and_partial_status(self):
        data = daily(['2024-01-01', '2024-01-03', '2025-01-01', '2026-01-15'], [100, 120, 200, 155])
        results = [analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=n) for n in (5, 10)]
        html = render_seasonal_report(results)
        parsed = TableParser()
        parsed.feed(html)
        self.assertEqual(parsed.rows[1], ['Jan', '155', '110', '200', '2/5', '3', '155', '1', '0', 'Partial calendar month'])
        self.assertEqual(parsed.rows[14][4], '2/10')
        self.assertEqual(parsed.rows[2][1], '—')
        self.assertIn('2021–2025', html)
        self.assertIn('2016–2025', html)
        self.assertIn('full historical calendar months', html)
        self.assertIn('12 significant digits', html)

    def test_escape_metadata_and_no_remote_dependencies(self):
        result = analyze_seasonality(daily(['2025-01-01'], [10]), as_of=date(2026, 1, 15), window_years=5)
        html = render_seasonal_report([result], title='<script>alert(1)</script>', unit='<img src=x onerror=x>', import_summary={'<unsafe>': 3})
        self.assertNotIn('<script', html)
        self.assertNotIn('<img', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;unsafe&gt;', html)
        self.assertNotRegex(html, r'(?:src|href)=[\"\']https?://')

    def test_chart_gaps_remain_separate_paths(self):
        result = analyze_seasonality(daily(['2025-01-01', '2025-03-01'], [10, 30]), as_of=date(2026, 3, 15), window_years=1)
        html = render_seasonal_report([result])
        svg = ElementTree.fromstring(re.search(r'<svg.*?</svg>', html, flags=re.S).group())
        baseline = [p for p in svg.findall('path') if p.attrib['stroke'] == '#2563eb'][0]
        self.assertEqual(baseline.attrib['d'].count('M '), 2)
        self.assertNotIn(' L ', baseline.attrib['d'])

    def test_empty_and_zero_negative_extreme_charts_are_valid(self):
        cases = [(['2027-01-01'], [10]), (['2025-01-01'], [0]),
                 (['2025-01-01', '2025-03-01'], [-10, 20]),
                 (['2025-01-01', '2025-03-01'], [-1e308, 1e308])]
        for dates, values in cases:
            with self.subTest(values=values):
                result = analyze_seasonality(daily(dates, values), as_of=date(2026, 3, 15), window_years=1)
                html = render_seasonal_report([result])
                for svg in re.findall(r'<svg.*?</svg>', html, flags=re.S):
                    self.assertNotRegex(svg, r'(?i)(?:nan|inf)')
                    ElementTree.fromstring(svg)

    def test_reject_incompatible_profiles_and_bad_metadata(self):
        data = daily(['2025-01-01', '2026-01-01'], [10, 20])
        a = analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=5)
        b = analyze_seasonality(data, as_of=date(2026, 2, 15), window_years=10)
        for results in ([], [object()], [a, a], [a, b]):
            with self.subTest(results=type(results)), self.assertRaises(ValueError):
                render_seasonal_report(results)
        for metadata in ({'a': -1}, {'a': True}, {1: 2}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                render_seasonal_report([a], import_summary=metadata)

    def test_fx_axis_fits_levels_and_is_shared_between_windows(self):
        data = daily(['2020-01-01', '2025-01-01', '2026-01-01'], [4.2, 4.3, 4.4])
        results = [analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=n) for n in (5, 10)]
        html = render_seasonal_report(results)
        charts = [ElementTree.fromstring(svg) for svg in re.findall(r'<svg.*?</svg>', html, flags=re.S)]
        labels = [[float(t.text) for t in svg.findall('text') if t.attrib.get('text-anchor') == 'end'] for svg in charts]
        self.assertEqual(labels[0], labels[1])
        # 8% of the 0.2 input range is 0.016: bounds 4.184 and 4.416.
        self.assertAlmostEqual(labels[0][0], 4.184)
        self.assertAlmostEqual(labels[0][-1], 4.416)
        positions = [float(c.attrib['cy']) for c in charts[1].findall('circle')]
        # Visible mean lines span 4.25–4.4 (not the min–max range 4.2–4.4).
        self.assertGreater(max(positions) - min(positions), 120)
        self.assertTrue(all(36 <= v <= 238 for v in positions))
        self.assertIn('Both profile charts use the same scale', html)

    def test_constant_negative_and_tiny_axes_stay_finite(self):
        for values in ([4.2], [-4.2], [0], [1e308], [float.fromhex('0x1.fffffffffffffp+1023')], [5e-324]):
            with self.subTest(values=values):
                result = analyze_seasonality(daily(['2025-01-01'], values), as_of=date(2026, 1, 15), window_years=1)
                html = render_seasonal_report([result])
                svg = ElementTree.fromstring(re.search(r'<svg.*?</svg>', html, flags=re.S).group())
                self.assertNotRegex(ElementTree.tostring(svg, encoding='unicode'), r'(?i)(?:nan|inf)')
                positions = [float(c.attrib['cy']) for c in svg.findall('circle')]
                self.assertTrue(all(36 <= v <= 238 for v in positions))
                labels = [float(t.text) for t in svg.findall('text') if t.attrib.get('text-anchor') == 'end']
                raw_labels = [t.text for t in svg.findall('text') if t.attrib.get('text-anchor') == 'end']
                self.assertEqual(len(set(raw_labels)), 5)
                self.assertTrue(all(pd.notna(v) and abs(v) != float('inf') for v in labels))
                axis_labels = [t for t in svg.findall('text') if t.attrib.get('text-anchor') == 'end']
                self.assertGreaterEqual(float(axis_labels[0].attrib['x']), max(len(label) for label in raw_labels) * 7)
                self.assertLessEqual(labels[0], values[0])
                self.assertGreaterEqual(labels[-1], values[0])
                if values[0] > 1:
                    self.assertGreater(labels[0], 0)
                elif values[0] < -1:
                    self.assertLess(labels[-1], 0)

    def test_narrow_range_axis_labels_remain_distinct(self):
        result = analyze_seasonality(daily(['2025-01-01', '2025-03-01'], [4.200001, 4.200003]), as_of=date(2026, 1, 15), window_years=1)
        html = render_seasonal_report([result])
        svg = ElementTree.fromstring(re.search(r'<svg.*?</svg>', html, flags=re.S).group())
        labels = [t.text for t in svg.findall('text') if t.attrib.get('text-anchor') == 'end']
        self.assertEqual(len(set(labels)), 5)
        self.assertGreater(float(labels[0]), 4.2)
        self.assertLess(float(labels[-1]), 4.200004)

    def test_legend_in_each_chart_names_lines_band_and_partial_marker(self):
        data = daily(['2025-01-01', '2026-01-01'], [4.2, 4.3])
        results = [analyze_seasonality(data, as_of=date(2026, 1, 15), window_years=n) for n in (5, 10)]
        html = render_seasonal_report(results)
        charts = [ElementTree.fromstring(svg) for svg in re.findall(r'<svg.*?</svg>', html, flags=re.S)]
        for window, svg in zip((5, 10), charts):
            legend = svg.find("g[@class='chart-legend']")
            self.assertIsNotNone(legend)
            text = ''.join(legend.itertext())
            self.assertIn(f'{window}-year average', text)
            self.assertIn('2026 monthly average', text)
            self.assertIn('Historical min–max', text)
            self.assertIn('not daily highs/lows', text)
            self.assertIn('partial month', text)
            self.assertEqual([line.attrib['stroke'] for line in legend.findall('line')], ['#2563eb', '#c45d11'])
            self.assertEqual(legend.find('rect').attrib['fill'], '#dbeafe')

    def test_cli_end_to_end_and_input_output_preservation(self):
        root = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(root / 'src'))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.csv'
            output = Path(folder) / 'result.html'
            content = 'date,instrument_id,value\n2024-01-01,A,100\n2024-01-03,A,120\n2025-01-01,A,200\n2026-01-15,A,155\n'
            source.write_text(content, encoding='utf-8')
            command = [sys.executable, str(root / 'examples/seasonal_demo.py'), str(source), '--instrument', 'A', '--as-of', '2026-01-15', '--output']
            success = subprocess.run(command + [str(output)], env=env, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            original_output = output.read_bytes()
            self.assertIn(b'Baseline average', original_output)
            for path in (output, source):
                rejected = subprocess.run(command + [str(path)], env=env, capture_output=True, text=True)
                self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(source.read_text(encoding='utf-8'), content)
            self.assertEqual(output.read_bytes(), original_output)


if __name__ == '__main__':
    unittest.main()
