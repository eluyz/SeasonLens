"""Run outside the checkout with the Python from an installed-wheel virtualenv."""
import argparse
import base64
from datetime import date
from importlib import metadata, resources
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile
import threading
from urllib.request import urlopen

import pandas as pd
import seasonlens
from seasonlens.app import create_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-version', required=True)
    args = parser.parse_args()
    assert metadata.version('seasonlens') == args.expected_version
    assert sys.prefix != sys.base_prefix, 'Use an isolated virtual environment.'
    assert Path(seasonlens.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), 'Imported source instead of installed wheel.'
    assets = resources.files('seasonlens')
    for name in ('dashboard.html', 'start_panel.html', 'start_ui.js', 'report_export.js',
                 'scientific_panel.html', 'workbook_import.js', 'template_download.js',
                 'quick_controls.css', 'report.css', 'vendor/xlsx.mini.min.js', 'vendor/LICENSE'):
        assert assets.joinpath(name).read_bytes(), name
    assert base64.b64decode(assets.joinpath('import_template.xlsx.b64').read_text().strip(), validate=True).startswith(b'PK\x03\x04')
    frame = pd.DataFrame({'date': pd.to_datetime(['2024-01-01', '2024-01-03', '2026-02-02']), 'value': [100., 120., 200.]})
    monthly = seasonlens.aggregate_monthly(frame)
    assert monthly.means.loc[2024, 1] == 110 and monthly.counts.loc[2024, 1] == 2
    assert monthly.means.loc[2025].isna().all() and (monthly.counts.loc[2025] == 0).all()
    html = seasonlens.render_dashboard({'INSTALL_SAMPLE': {'frame': frame, 'title': 'Invented install check', 'unit': 'EUR/t', 'source': 'SYNTHETIC', 'quote_semantics': 'Invented observations'}}, as_of=date(2026, 10, 6))
    assert 'id="seasonlens-start"' in html and 'initSeasonLensStartGuide' in html
    assert 'id="report-export-panel"' in html and '@@' not in html
    script_dir = Path(sysconfig.get_path('scripts'))
    suffix = '.exe' if os.name == 'nt' else ''
    data_command = script_dir / ('seasonlens-data' + suffix)
    app_command = script_dir / ('seasonlens-app' + suffix)
    subprocess.run([str(data_command), '--help'], check=True, capture_output=True)
    subprocess.run([str(app_command), '--help'], check=True, capture_output=True)
    with tempfile.TemporaryDirectory(prefix='seasonlens-install-check-') as temporary:
        db = Path(temporary) / 'private.sqlite'
        subprocess.run([str(data_command), '--db', str(db), 'init'], check=True, capture_output=True)
        server = create_server(db, as_of=date(2026, 10, 6), port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            assert server.server_address[0] == '127.0.0.1'
            with urlopen(f'http://127.0.0.1:{server.server_port}/', timeout=10) as response:
                empty_html = response.read().decode('utf-8')
            assert 'id="browser-file"' in empty_html and 'id="upload"' in empty_html
            assert 'initSeasonLensStartGuide' in empty_html and '@@' not in empty_html
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    print(json.dumps({'installed_version': metadata.version('seasonlens'), 'python': sys.version.split()[0], 'pandas': metadata.version('pandas'), 'numpy': metadata.version('numpy'), 'checks': 'wheel assets, arithmetic, CLI entry points, empty private database and loopback UI passed'}))


if __name__ == '__main__':
    main()
