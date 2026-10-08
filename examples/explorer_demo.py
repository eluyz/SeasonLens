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
    corn = pd.DataFrame({'date':days,'value':[150+i*.012+14*math.sin(i/56)+5*math.cos(i/23) for i in t]})
    rapeseed = pd.DataFrame({'date':days,'value':[360+i*.025+40*math.sin(i/66)+16*math.cos(i/29) for i in t]})
    fx = pd.DataFrame({'date':days,'value':[4.25+.15*math.sin(i/155)+.025*math.cos(i/13) for i in t]})
    eur_usd = pd.DataFrame({'date':days,'value':[1.11+.10*math.sin(i/191)+.013*math.cos(i/31) for i in t]})
    usd_pln = pd.DataFrame({'date':days,'value':fx.value / eur_usd.value})
    return {
        'SYNTHETIC_GRAIN':dict(frame=grain,title='Wheat · sample',unit='EUR/t',source='SYNTHETIC',quote_semantics='Invented daily wheat observations; no real contracts'),
        'SYNTHETIC_CORN':dict(frame=corn,title='Corn · sample',unit='EUR/t',source='SYNTHETIC',quote_semantics='Invented daily corn observations; no real contracts'),
        'SYNTHETIC_RAPESEED':dict(frame=rapeseed,title='Rapeseed · sample',unit='EUR/t',source='SYNTHETIC',quote_semantics='Invented daily rapeseed observations; no real contracts'),
        'EUR_PLN':dict(frame=fx,title='Synthetic EUR/PLN',unit='PLN per EUR',source='SYNTHETIC',quote_semantics='Invented FX values; not ECB observations'),
        'EUR_USD':dict(frame=eur_usd,title='Synthetic EUR/USD',unit='USD per EUR',source='SYNTHETIC',quote_semantics='Invented FX values; not ECB observations'),
        'USD_PLN':dict(frame=usd_pln,title='Synthetic USD/PLN',unit='PLN per USD',source='SYNTHETIC',quote_semantics='Same-date synthetic EUR/PLN divided by synthetic EUR/USD; not ECB observations'),
    }


if __name__ == '__main__':
    output=Path('examples/explorer_demo.html')
    output.write_text(render_dashboard(demo_series(),as_of=date(2026,10,6),title='SeasonLens — synthetic demo'),encoding='utf-8')
    print('Synthetic explorer generated. Every observation is invented.')
