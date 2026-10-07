"""Synthetic ECB XML fixtures; no live prices or external network calls."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from datetime import date
from seasonlens.ecb import RECENT_URL, HISTORY_URL, fetch_ecb_rates, parse_ecb_xml, update_ecb
from seasonlens.storage import list_series, read_series


def xml(body):
    return ('<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube>' + body + '</Cube></gesmes:Envelope>').encode()


SYNTHETIC_XML = xml('<Cube time="2024-01-03"><Cube currency="PLN" rate="4.4"/><Cube currency="USD" rate="1.1"/></Cube><Cube time="2024-01-02"><Cube currency="PLN" rate="4.2"/><Cube currency="USD" rate="1.2"/></Cube>')


class ECBTests(unittest.TestCase):
    def test_same_date_hand_derived_quotes_and_sorting(self):
        frames = parse_ecb_xml(SYNTHETIC_XML)
        self.assertEqual(set(frames), {"EUR_PLN", "EUR_USD", "USD_PLN"})
        self.assertAlmostEqual(frames["USD_PLN"].loc[0, "value"], 3.5)
        self.assertEqual(frames["USD_PLN"].loc[1, "value"], 4.0)
        self.assertEqual(frames["EUR_PLN"]["value"].tolist(), [4.2, 4.4])
        self.assertEqual(str(frames["USD_PLN"].loc[1, "date"].date()), "2024-01-03")

    def test_malformed_or_incomplete_observations_reject(self):
        bodies = [
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="4.4"/></Cube>',
            '<Cube time="bad"><Cube currency="PLN" rate="4.4"/><Cube currency="USD" rate="1.1"/></Cube>',
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="4.4"/><Cube currency="PLN" rate="4.5"/><Cube currency="USD" rate="1.1"/></Cube>',
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="4.4"/><Cube currency="USD" rate="0"/></Cube>',
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="nan"/><Cube currency="USD" rate="1.1"/></Cube>',
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="4.4"/><Cube currency="USD" rate="-1.1"/></Cube>',
            '<Cube time="2024-01-01"><Cube currency="PLN" rate="1e308"/><Cube currency="USD" rate="1e-308"/></Cube>',
            '',
        ]
        for body in bodies:
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_ecb_xml(xml(body))
        with self.assertRaises(ValueError):
            parse_ecb_xml(b'<not-ecb/>')
        with self.assertRaises(ValueError):
            parse_ecb_xml(b'<!DOCTYPE x [<!ENTITY a "x">]><x/>')
        with self.assertRaises(ValueError):
            parse_ecb_xml(b'<broken')

    def test_duplicate_dates_reject_even_with_equal_values(self):
        cube = '<Cube time="2024-01-01"><Cube currency="PLN" rate="4.4"/><Cube currency="USD" rate="1.1"/></Cube>'
        with self.assertRaisesRegex(ValueError, "duplicate observation dates"):
            parse_ecb_xml(xml(cube + cube))

    def test_fetch_fixed_official_urls_and_explicit_timeout(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = SYNTHETIC_XML
        with patch('seasonlens.ecb.urlopen', return_value=response) as opener:
            fetch_ecb_rates(timeout=9)
            self.assertEqual(opener.call_args.args[0].full_url, RECENT_URL)
            self.assertEqual(opener.call_args.kwargs['timeout'], 9)
            fetch_ecb_rates(history=True)
            self.assertEqual(opener.call_args.args[0].full_url, HISTORY_URL)
        for invalid in (0, -1, float('inf'), True):
            with self.assertRaises(ValueError):
                fetch_ecb_rates(timeout=invalid)

    def test_update_is_atomic_and_distinguishes_reference_semantics(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'private.sqlite'
            with patch('seasonlens.ecb.fetch_ecb_rates', return_value=parse_ecb_xml(SYNTHETIC_XML)):
                summaries = update_ecb(path)
            self.assertEqual(len(summaries), 3)
            self.assertAlmostEqual(read_series(path, 'USD_PLN').loc[0, 'value'], 3.5)
            self.assertEqual(read_series(path, 'USD_PLN').loc[1, 'value'], 4.)
            records = {item['series_id']: item for item in list_series(path)}
            self.assertIn('Same-date derived', records['USD_PLN']['quote_semantics'])
            self.assertEqual(records['EUR_PLN']['source'], 'ECB_REFERENCE')

    def test_future_provider_dates_reject_before_any_database_write(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'private.sqlite'
            with patch('seasonlens.ecb.fetch_ecb_rates', return_value=parse_ecb_xml(SYNTHETIC_XML)), self.assertRaisesRegex(ValueError, 'after the update cutoff'):
                update_ecb(path, as_of=date(2024, 1, 2))
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
