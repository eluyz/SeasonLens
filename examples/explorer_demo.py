"""Generate an entirely invented public explorer, including invented FX."""
from datetime import date
import math
from pathlib import Path
import pandas as pd
from seasonlens.dashboard import render_dashboard


def demo_series():
    days = pd.bdate_range('2014-01-01','2026-10-08')
    t = range(len(days))
    grain = pd.DataFrame({'date':days,'value':[170+i*.015+18*math.sin(i/42)+7*math.cos(i/17) for i in t]})
    fx = pd.DataFrame({'date':days,'value':[4.25+.15*math.sin(i/155)+.025*math.cos(i/13) for i in t]})
    return {
        'SYNTHETIC_GRAIN':dict(frame=grain,title='Synthetic grain',unit='EUR/t',source='SYNTHETIC',quote_semantics='Invented daily grain observations; no real contracts'),
        'EUR_PLN':dict(frame=fx,title='Synthetic EUR/PLN',unit='PLN per EUR',source='SYNTHETIC',quote_semantics='Invented FX values; not ECB observations'),
    }


if __name__ == '__main__':
    output=Path('examples/explorer_demo.html')
    output.write_text(render_dashboard(demo_series(),as_of=date(2026,10,6),title='SeasonLens — synthetic demo'),encoding='utf-8')
    print('Synthetic explorer generated. Every observation is invented.')
