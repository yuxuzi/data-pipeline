# Changelog

All notable changes to this pack are recorded here.

## 1.1.0

- The manifest declares `categories` and `keywords` for pytemplate-hub's filters and search
  (needs pytemplate-uv 3.4 or later).
- The README creates projects with the hub's short `-h yuxuzi/data-pipeline@v1.1.0` command.

## 1.0.0

- Initial release: `etl` (DuckDB) and `etl-polars` (Polars) profiles. Each has typed extract, validate, transform, and load steps, sample data, a `run` command, and offline tests, with no optional components.
