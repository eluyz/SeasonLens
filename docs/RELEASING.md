# Release a reviewed version

Ordinary code pushes do not publish releases. The separate release workflow runs only after an explicit `.github/release-request.json` change on main or a manual retry of that same reviewed request. It uses the repository's built-in, temporary GitHub Actions token; no personal token or package-index credential is required.

1. Bump `pyproject.toml` and the ECB User-Agent version; write `docs/releases/vX.Y.Z.md`. Update installation and example instructions. Use invented public examples only.
2. Run the analytical suite and isolated installed-wheel checks. Both Python 3.10 and 3.12 Linux checks must pass. Rebuild public pages with the existing candidate workflow, inspect the candidate diff and promote it with a checked fast-forward. Verify the deployed demo and walkthrough before requesting publication.
3. Record the checks in STATUS.md. Freeze the reviewed main commit. In a new commit, change **only** `.github/release-request.json`:

```json
{"version": "0.1.0", "expected_parent": "<full SHA of the reviewed parent commit>"}
```

The helper rejects a changed version, wrong parent or any other file in that request commit. The version must be an explicit `0.x.y` release. The workflow checks that main still points to its exact commit before tag creation and again before publication.

4. The workflow runs tests, checks generated files against source, builds wheel/source distributions and verifies the wheel in an isolated environment outside the checkout. It packages a fixed allowlist of invented browser files and both software licenses, then computes SHA256SUMS.
5. A new annotated tag points to that checked request commit. A **draft** release receives exactly four assets: wheel, source tarball, frozen browser ZIP and SHA256SUMS. Asset names, uploaded state, sizes and GitHub SHA-256 digests must match before the draft becomes public.
6. Verify the published release, its tag target, attached assets and downloadable source. Add the actual workflow IDs and verification to STATUS.md after publication. Do not move the tag to that later documentation commit.

## Recover an interrupted publication

First inspect the job, tag and release. A retry can reuse a tag only if it resolves to the **same workflow commit**. A matching unpublished draft can replace the four controlled assets; unexpected assets, corrupt uploads or a moved main branch block publication. Already published releases are never modified by this workflow; use a new version for corrections. No tag is forced or deleted.

If main moved before publication, do not loosen the head/parent guards. Review the new main and prepare a new version/request, or restore the still-authorized reviewed state through an ordinary reviewed change. A tag-creation permission failure is a repository configuration blocker, not a reason to add or expose a personal token.

If the original build/tag/asset upload succeeded but publication itself failed, `Finalize pinned existing draft` provides a narrower recovery after reviewing an operational fix. Commit that fix first, then change **only** `.github/release-finalization.json` in a separate commit. Declare `version`, `expected_parent` (the reviewed fix commit), `tag_commit` (the original unchanged request commit), the exact existing `release_id`, and four `assets` entries with their observed `name`, `id`, `size` and `digest`. Do not guess these identities or copy them from another release.

The finalizer verifies the original request-only commit and its version/parent, ancestry, unchanged tag, current request-only main, matching unpublished draft and pinned asset inventory. It downloads the existing files via authenticated asset IDs, checks bytes and SHA256SUMS, compares the frozen browser files against the unchanged tag and installs the downloaded wheel in isolation. It rechecks main/tag/draft/assets immediately before publishing **that draft by numeric ID**. It never creates/moves a tag, replaces an asset or modifies a published release. Reading draft metadata by ID avoids the tag lookup that returned404 in the first0.1.0 attempt.

The release workflow does not publish to PyPI, change account permissions, enable a data feed or schedule a market-data job. Live demo updates are handled separately by GitHub Pages; the release ZIP remains frozen.
