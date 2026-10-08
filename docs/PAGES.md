# Public SeasonLens demo

The public site at https://eluyz.github.io/SeasonLens/ is a static demonstration built only from deterministic invented prices and FX quotes. It requires no user account, installation, API key or server-side Python. The sample analysis cutoff is fixed at 2026-10-06; it is not a live market-data service.

## Enable GitHub Pages

The deployment files are `docs/index.html`, `docs/.nojekyll` and `docs/sample_prices.csv`. A repository administrator must enable publishing:

1. Open https://github.com/eluyz/SeasonLens/settings/pages.
2. Under Build and deployment, select Deploy from a branch.
3. Select `main` and `/docs`, then Save.
4. Check the deployment status and open the exact URL shown by GitHub. The standard expected project URL is https://eluyz.github.io/SeasonLens/; it is not considered live until deployment succeeds.

After activation, commits to the publishing source update the site. Deployment/build results are visible in the repository Actions tab. No custom domain is required. Do not publish private databases, imported market data or private rendered reports to this directory.

## Rebuild

From the repository root with the package dependencies installed:

```bash
PYTHONPATH=src python3 examples/build_pages.py
```

The builder accepts no input database or market-data path. It imports `demo_series()` from the synthetic example, checks SYNTHETIC provenance, generates the same Python analytics as the local explorer, removes the local importer and its server-request code, and writes a standalone page and a synthetic sample CSV. Commit the regenerated files to publish an update after Pages is enabled.

### Build on GitHub

The `Build public demo` workflow runs tests and regenerates both invented example pages on GitHub when their source changes on `main`, or when manually started on `main`. It saves generated files on a unique `automation/public-demo-<run>-<attempt>` branch using GitHub's temporary repository token. It does not update `main` or deploy the site. Promote the successful candidate with a checked fast-forward through an authorized user/app connection; this triggers the existing branch-based Pages deployment. A push using the workflow token alone does not trigger Pages. No personal token, private database or market-data input is required.

## Features and limits

Sample instruments: wheat, corn and rapeseed (EUR/t or PLN/t), plus EUR/PLN, EUR/USD and USD/PLN. All series share synthetic observation dates; USD/PLN is calculated per date as EUR/PLN divided by EUR/USD. These are invented values, not exchange prices or ECB data.

The site includes the ten-year monthly price matrix, five-year yearly comparisons, six technical lines, seasonal profiles, coverage, exact-date synthetic PLN conversion and full-series CSV export. All demo observations are invented, including currency quotes. Commodity matrix values display zero decimals; FX values display three. Wide charts and tables scroll horizontally on narrow screens. Advanced seasonal analyses are initially collapsed.

The static page accepts an explicitly mapped XLSX master file or one CSV series in browser memory, using a chosen cutoff and supported dates. User files are not uploaded, saved to a database or retained on reload. Imported series are labelled USER_FILE and cannot overwrite the invented samples. Private SQLite persistence remains available in the local Python app. The page makes no data-upload requests and loads no external scripts, analytics or fonts. GitHub Pages still receives normal website requests; this is not a claim of anonymous hosting. A content security policy disables connection requests from page scripts.

The public explorer now accepts XLSX master files and single-series CSV entirely within the browser. The vendored reader and original license are included in the package; no runtime CDN is used. The only localStorage item holds whitelisted view preferences, not imported files or observations. Imported series disappear on reload.
