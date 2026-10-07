"""Build the GitHub Pages demo exclusively from deterministic invented series.

Run from any directory: PYTHONPATH=/path/to/SeasonLens/src python build_pages.py.
This builder accepts no market-data input or database path.
"""
from datetime import date
from pathlib import Path
import re

from explorer_demo import demo_series
from seasonlens.dashboard import render_dashboard


def build_public_demo():
    series = demo_series()
    if not all(entry.get('source') == 'SYNTHETIC' for entry in series.values()):
        raise ValueError('The public demo accepts invented observations only.')
    html = render_dashboard(series, as_of=date(2026, 10, 6),
                            title='SeasonLens — explore seasonal prices')
    html = html.replace('Explorer v7 · private local analysis', 'Public demo · invented data')
    html = html.replace('<head>', '<head><meta name="description" content="Explore monthly price averages, seasonality and technical indicators with SeasonLens. Free open-source tools; this demo uses invented data.">'
                        '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; connect-src \'none\'; object-src \'none\'; base-uri \'none\'; form-action \'none\'">')
    intro = '''<section class="welcome" aria-label="About this demo">
<p class="eyebrow">OPEN SOURCE · NO ACCOUNT REQUIRED</p>
<h2>Your prices. Clear seasonal context.</h2>
<p>Compare monthly averages, explore seasonal patterns and inspect six technical lines. Choose a sample instrument below to get started.</p>
<p class="notice"><strong>Every price and currency quote in this demo is invented.</strong> These are sample observations, not live market prices or trading recommendations.</p>
<nav class="demo-nav" aria-label="Explore SeasonLens"><a href="#matrix">Explore sample data</a><a href="#own-data">Use your own data locally</a><a href="https://github.com/eluyz/SeasonLens">Source code</a></nav>
<p class="muted">On a phone, swipe wide tables and charts horizontally. No installation is needed to explore this sample.</p>
</section>'''
    controls = '<div class="panel controls">'
    if html.count(controls) != 1:
        raise ValueError('Expected exactly one explorer controls panel.')
    html = html.replace(controls, intro+controls, 1)
    html = html.replace('<section><h2>Monthly average prices — last ten', '<section id="matrix"><h2>Monthly average prices — last ten', 1)
    html = html.replace('<section><h2>Monthly average prices — last five', '<section id="year-comparison"><h2>Monthly average prices — last five', 1)
    html = html.replace('<section><h2>Technical analysis', '<section id="technical"><h2>Technical analysis', 1)
    html = html.replace('<div class="checks" id="profile-controls">', '<details class="advanced"><summary>More seasonal analysis and coverage</summary><div class="checks" id="profile-controls">', 1)
    html = html.replace('<section id="import-panel">', '</details><section id="import-panel">', 1)
    local_panel = '''<section id="own-data"><h2>Use your own data</h2>
<p>This public version explores the sample data above. Browser file import is not available yet. To analyze a private CSV today, run the local SeasonLens app using the instructions in the repository.</p>
<p><a href="sample_prices.csv" download>Download an invented sample CSV</a> · <a href="https://github.com/eluyz/SeasonLens#interactive-explorer-and-private-database">Local app instructions</a> · <a href="https://github.com/eluyz/SeasonLens/issues">Report an issue</a></p>
<p class="muted">The sample explorer makes no data-upload requests. Visiting this website still uses GitHub Pages hosting. Private market data should stay in your own local app.</p></section>'''
    html, count = re.subn(r'<section id="import-panel">.*?</section>', local_panel, html, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Local importer panel was not found.')
    start = html.index('if(!localImport){')
    html.index('if(Object.keys(data).length){choose()}', start)
    html = html[:start] + 'choose();\n</script></body></html>\n'
    html = re.sub(r'<footer>.*?</footer>', '<footer>SeasonLens · MIT-licensed open-source software · all demo observations are invented. Statistics summarize historical sample values, not forecasts. Counts do not certify complete sessions. The sample cutoff is fixed; this demo does not collect market data.</footer>', html, count=1, flags=re.S)
    styles = '''
.welcome{background:linear-gradient(120deg,#eff6ff,#fff)}.eyebrow{letter-spacing:.08em;font-size:12px;font-weight:700;color:#1d4ed8}.welcome h2{font-size:28px}.demo-nav{display:flex;gap:10px;flex-wrap:wrap}.demo-nav a{padding:10px 14px;border:1px solid #cbd5e1;border-radius:8px;text-decoration:none;background:#fff}.demo-nav a:first-child{background:#1d4ed8;color:#fff;border-color:#1d4ed8}.advanced{background:#fff;border:1px solid #dde5f0;border-radius:14px;padding:20px;margin:20px 0}.advanced>summary{font-size:18px}.table-wrap{max-width:100%;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}.controls select,.controls button{min-height:44px}section{scroll-margin-top:15px}#daily,#fiveyear{overflow-x:auto}.price-matrix th:first-child{min-width:95px}
@media(max-width:700px){.welcome h2{font-size:24px}.controls{display:grid;grid-template-columns:1fr 1fr;gap:12px}.controls label{min-width:0}.controls select{width:100%}.controls button{grid-column:1/-1}.checks{gap:12px}.checks label{padding:5px 0;min-height:44px}#daily svg{min-width:760px}#fiveyear svg{min-width:760px}.table-wrap{margin-bottom:8px}.advanced{padding:14px}.advanced svg{min-width:620px}.advanced section{overflow-x:auto}.demo-nav a{flex:1 1 180px;text-align:center}}
'''
    html = html.replace('</style>', styles+'</style>', 1)
    if any(marker in html for marker in ('fetch(', '/import', 'type="file"', '@@DATA@@', '@@LOCAL@@', '@@ASOF@@')):
        raise ValueError('Unexpected local import or unexpanded template in public demo.')
    return html, series


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    output = root / 'docs'
    output.mkdir(exist_ok=True)
    html, series = build_public_demo()
    (output / 'index.html').write_text(html, encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    sample = series['SYNTHETIC_GRAIN']['frame']
    sample.loc[sample.date.dt.date <= date(2026, 10, 6)].to_csv(output / 'sample_prices.csv', index=False, date_format='%Y-%m-%d')
    print('Public Pages demo built from invented observations only.')
