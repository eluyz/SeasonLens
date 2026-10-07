# Data policy

Decision date: 2026-10-07. This policy defines the project's data boundaries; it does not grant rights to third-party data.

## Public project and private inputs

SeasonLens code is public and MIT licensed. Public examples currently use invented, clearly labelled synthetic values.

Imported market-price files, raw responses, source identifiers and evidence of usage permissions are private by default. Keep them outside the repository or in ignored local directories. Do not include private provider names, account details or file-specific provenance in public project documentation. Preserve accurate provenance privately; do not replace it with an invented source.

Private storage does not itself authorize use of a dataset. Users must have the rights needed for their intended local processing. Sharing an input with an external service is a separate use to assess.

Charts, monthly averages, seasonal profiles, CSV exports and HTML reports derived from restricted inputs are private by default too. Removing the input file, hiding underlying chart values or changing the calculation does not establish redistribution rights. Public output requires a separate assessment of the applicable terms.

The root directories `private/`, `data/`, `outputs/` and `exports/` are ignored by Git. This is a safeguard against accidental additions, not access control: it does not protect tracked files, forced additions, other paths or files attached to issues. Place approved public examples under `examples/` with dataset-specific attribution and terms.

## Foreign exchange: European Central Bank

The selected source for future public FX examples is the [ECB's euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html), obtained directly from the ECB. History is offered as CSV/XML.

Under the [ECB copyright conditions](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html), reproduce information accurately, identify the ECB as the source and explicitly state modifications or calculations. For sold documents, disclose that the source information is available free from the ECB. These data retain the ECB's conditions; the code's MIT license does not replace them.

Label values as daily reference rates, not exchange closes or executable quotes. ECB quotations use EUR as the base currency. A calculated USD/PLN rate is PLN per EUR divided by USD per EUR; label it as a calculation from ECB reference rates.

No ECB downloader or public FX dataset is implemented in this checkpoint.

## MATIF: separate Euronext candidate

[Euronext Trades Files](https://marketdata.euronext.com/data-reporting-service/trades-file) is a candidate for collecting new commodity-derivative transactions directly from Euronext. The portal offers delayed CSV files from a short current/previous-session window; it is not a confirmed free historical archive.

The portal's [Delayed Trade Data terms](https://www.euronext.com/sites/default/files/stld/terms_and_conditions_for_delayed_data.pdf) contemplate distribution with source attribution where reasonably practicable and the prescribed prominent disclaimer. Distribution for a fee or intended commercial benefit requires an agreement with Euronext. Before any public dataset or chart is added, check that its origin, use and distribution meet the applicable terms and include the required notices. Do not label Euronext data MIT or CC0.

This route applies only to data actually obtained under those terms. It does not clear an existing MATIF history obtained from another supplier. Keep those imported files private. Last-trade prices are not automatically official settlement prices; any aggregation and contract-roll method must be documented.

No Euronext downloader, historical archive or public market-price dataset is implemented in this checkpoint.
