# Data pipelines

A reference pack provided by the pytemplate-hub maintainer.

Two small, typed extract-transform-load pipelines in Python, for [pytemplate-uv](https://github.com/yuxuzi/pytemplate-uv).
Each reads a CSV, validates it, summarises it, and writes Parquet. The steps are plain typed
functions with tests, the sample data is included, and a Typer `run` command runs the whole thing.
Each generated project uses uv, ruff, mypy in strict mode, and pytest, and has an `AGENTS.md` and a
`CLAUDE.md` for coding agents. The pack has no optional components.

## What you get

An `etl` project looks like this (the `etl-polars` project has the same shape, without the SQL file):

```text
my-pipeline/
  .copier-answers.yml
  .gitignore
  .pytemplate.toml
  AGENTS.md
  CLAUDE.md
  README.md
  pyproject.toml
  data/
    sample.csv
  my_pipeline/
    __init__.py
    cli.py
    pipeline.py
    transform.sql
  tests/
    test_cli.py
    test_pipeline.py
  uv.lock
```

## Profiles

| Profile | Kind | What you get |
| --- | --- | --- |
| `etl` | cli | DuckDB (`duckdb>=2.0.1`). Extract loads the CSV into a table with fixed types, validate checks the rows, transform runs one SQL aggregation from `transform.sql`, and load writes Parquet. A Typer `run --input --output` command runs it. |
| `etl-polars` | cli | The same pipeline shape with Polars (`polars>=2.1.0`). The transform is one Polars expression chain in `pipeline.py`. |

Both profiles' `security_posture` says what they read and write. They read and write local files
only, need no credentials or services, and validate input before anything is loaded.

## Create a project

```bash
uvx pytemplate-uv@latest create my-pipeline -p etl -h yuxuzi/data-pipeline@v1.1.0 -y
```

`-h` (`--hub`, pytemplate-uv 3.5 or later) reads the commit and digest that
[pytemplate-hub](https://yuxuzi.github.io/pytemplate-hub/) checked for this tag, and refuses the pack if
anything changed. For CI or offline use, copy the fully pinned command from the pack's listing there.

Replace `etl` with `etl-polars` for the Polars version. The hub's listing page also gives
`--template-commit` and `--template-digest` values, which refuse the pack if it has changed.

Then run it:

```bash
cd my-pipeline
uv sync
uv run my-pipeline run
```

## What the generated checks run

Each project's lifecycle checks, which pytemplate-uv runs after rendering, are:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy <package> tests
uv run pytest
```

The tests are offline. They run the pipeline on the sample data in a temporary folder and check
each validation failure. The checks do not scan dependencies or code for security problems.
The projects need no secrets or services.

## Make your own pack from this one

1. Fork or copy this repository.
2. Change `id` in `pytemplate-pack.toml` to your own pack name.
3. Edit a profile under `<profile>/template/` and its `profile.toml`. To add a profile, add it to
   the `profile` choices in `questions.yml`.
4. Check it:
   ```bash
   uvx pytemplate-uv@latest list-profiles --template .
   uvx pytemplate-uv@latest create t -p <profile> --template . -y -o <temp-dir>
   ```
   Then run `uv run pytest` in the new project.
5. Tag a release, then list the pack on [pytemplate-hub](https://github.com/yuxuzi/pytemplate-hub)
   by adding it to `docs/authors.md`.

## License

MIT. See [LICENSE](LICENSE).
