# Versioning and releases

This repository publishes **two things on two schedules**: the MusiCorpus specification, which is a document, and the `musicorpus` python package, which is code. They are released independently, from the same git history, under two families of tags.

Keeping them together is deliberate — the validator and the clauses it enforces stay honest by sitting next to each other — but it means the tag namespace is shared, and that has to be managed rather than assumed.


## Three numbers that are easy to confuse

| Number | What it versions | Where it lives | Moves when |
| --- | --- | --- | --- |
| **The specification version** | The document: what a conformant dataset looks like. `1.0` today. | The document's title, and the `specification-*` git tags. | The rules change. Rarely, and never silently — datasets already published claim a version. |
| **The package version** | The code: the CLI, the python API. Semver, derived from the git tags, written down nowhere. | Computed at build time from `git describe`. | Every commit, in effect — see below. |
| **`musicorpus_version`** | Which specification version *a dataset* claims to follow. | The `musicorpus.json` manifest inside each dataset. | The dataset is rebuilt against a newer specification. |

The package exports the specification version it implements as `musicorpus.SPECIFICATION_VERSION`, so a consumer can compare it against what a dataset claims:

```python
import musicorpus

if dataset.manifest.musicorpus_version != musicorpus.SPECIFICATION_VERSION:
    ...  # written against a different version of the specification
```

The first two are independent on purpose. Publishing a new version of the package does not re-version the specification, and a dataset built last year against specification 1.0 does not become wrong because the package moved to 0.4.


## The package version comes from the tags

`pyproject.toml` declares the version *dynamic* and lets [hatch-vcs](https://github.com/ofek/hatch-vcs) derive it:

```toml
[tool.hatch.version]
source = "vcs"
raw-options = { git_describe_command = "git describe --dirty --tags --long --match v[0-9]* --abbrev=8" }
```

**The `--match v[0-9]*` is load-bearing and must not be removed.** setuptools-scm's default is `--match *[0-9]*`, which matches any tag containing a digit — including `specification-1.1`. With the default, tagging a new version of the *document* would silently become the version of the *code*:

```
$ git tag specification-1.1
$ git describe --dirty --tags --long --match '*[0-9]*'   # the default
specification-1.1-0-g24c373f6                            # ← would become the package version
$ git describe --dirty --tags --long --match 'v[0-9]*'   # what we configure
fatal: No names found, cannot describe anything          # ← correctly ignored
```

That is the whole cost of keeping both in one repository, and one line pays it.

What you get out:

| Where you are | Version built |
| --- | --- |
| Exactly on `v0.1.0`, clean tree | `0.1.0` |
| 3 commits after it | `0.1.1.dev3+g2d478f1` |
| 3 commits after it, with uncommitted edits | `0.1.1.dev3+g2d478f1.d20260731` |
| Before the first tag | `0.1.dev48+geeee320` |

The `.dev` number counts commits since the tag, so it rises monotonically and every commit gets a distinct, correctly-ordered version. The `0.1.1` part is a *guess* — setuptools-scm assumes the next release bumps the patch. Only the ordering matters.


### Why not just write the version down

Because `pip` decides whether to reinstall by comparing **version strings, and nothing else**. It records the commit it installed from in `direct_url.json` and then ignores it when making that decision. With a hand-maintained version that stays `0.1.0` across a development cycle:

| Situation | What pip does |
| --- | --- |
| Same version, new commit, plain install | **nothing, silently** |
| Same version, new commit, `pip install -U` | **nothing, silently** — `-U` does not help |
| Different version, plain install | installs it, no `-U` needed |
| `--force-reinstall --no-deps` | always reinstalls |

The first two rows are the trap, and this package is installed from a git URL, which is exactly where it bites: a colleague reinstalls from a newer commit, pip prints nothing alarming, and they keep running the old code.


## Releasing the package

Say the package is going to `0.2.0`.

1. Move `CHANGELOG.md` entries from *Unreleased* into a `## 0.2.0 — 2026-07-31` section.
2. Commit that. There is **no version to bump** — that is the point of deriving it.
3. Tag and push:

   ```bash
   git tag v0.2.0
   git push origin main v0.2.0
   ```

4. Create the release page, with that changelog section as its notes:

   ```bash
   gh release create v0.2.0 --title "musicorpus 0.2.0" --notes-file notes.md
   ```

5. Sanity-check that the tag builds clean, with no `.dev` suffix:

   ```bash
   pip download --no-deps -d /tmp/check \
     'musicorpus @ git+https://github.com/OmniOMR/musicorpus.git@v0.2.0'
   ```

Tags for the code are `v`-prefixed. Nothing else may be.


## Releasing the specification

The document is released under a `specification-*` tag, and the rendered PDF is attached to that release as an asset. `musicorpus export omniomr` downloads that asset into the dataset it builds, which is how a published dataset carries the specification it was built against.

1. Settle the document in `spec/musicorpus-specification.md` and update its title to the new version.
2. Render it:

   ```bash
   python3 spec/build.py     # needs pandoc and chromium
   ```

3. Tag and push. **Do not use a `v` prefix** — that namespace belongs to the code:

   ```bash
   git tag specification-1.1
   git push origin main specification-1.1
   ```

4. Create the release and attach the PDF, named with the version and the date:

   ```bash
   gh release create specification-1.1 \
     --title "MusiCorpus Specification 1.1" \
     spec/musicorpus-specification.pdf#musicorpus-specification_1.1_2026-07-31.pdf
   ```

5. Update `DOWNLOAD_URL` in `src/musicorpus/exporters/omniomr/download_specification_pdf.py` and `SPECIFICATION_VERSION` in `src/musicorpus/__init__.py`, then release the package too — a package that implements a specification version should say which one.

The existing 1.0 release is tagged `specification`, without a version in the tag name. That was fine when there was one; the next one should be `specification-1.1` so the tags stay orderable and the 1.0 tag stays immutable.


## When the build needs git

The package version is computed at build time by running `git`, so the build needs a repository:

- **A source archive has no history.** GitHub's "Download ZIP", `git archive`, or a `COPY` into a Docker image that excludes `.git` all fail to build with `unable to detect version`. Installing from a `git+https://` link is fine — pip clones, so the history is there.
- **It needs the tags, not just the history.** A normal `git clone` fetches them; a shallow or `--no-tags` clone, typical in CI, does not. This is why the workflow checks out with `fetch-depth: 0`.
- **The escape hatch is `SETUPTOOLS_SCM_PRETEND_VERSION`**, which forces a version when there is no repository to read. The more precise `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_<NAME>` form does *not* work under hatch-vcs, which does not pass the distribution name through; use the plain variable.
- **The `+g<sha>` local segment cannot be uploaded to PyPI.** It never appears on a tagged commit, so it is not a problem today, but it is one of the two things to settle before publishing to an index. The other is the git-URL dependency on lmx, which PyPI rejects outright — which is why lmx sits in an extra rather than in the base dependencies.


## The changelog

[CHANGELOG.md](../CHANGELOG.md) is in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) form: an *Unreleased* section at the top that accumulates entries as work lands, and one section per released version below it. It is the source text for the GitHub release notes, and it is the only human-written record of what a version contains — the tag says when, the changelog says what.

Entries are written for whoever installs the package, so they describe behaviour and contracts rather than commits. Changes to the specification are recorded there too, marked as such, because a reader wanting to know what moved should not have to look in two places.
