# link-pd-code

`link-pd-code` converts one or more ordered closed polygonal components in
three-dimensional space into a planar diagram (PD) code. The implementation is
pure C++17 and supports Windows, Linux, and macOS without Git submodules or
runtime downloads.

## Build

```sh
python build.py
```

Use `--cxx` or `CXX` to select a g++-style compiler:

```sh
python build.py --cxx /path/to/g++ --portable
```

The executable is written to `build/link-pd-code` or
`build/link-pd-code.exe`.

## Usage

```sh
build/link-pd-code --input coordinates.txt --output pd.txt
```

If `--input` is omitted, coordinates are read from stdin. If `--output` is
omitted, the PD code is written to stdout.

Important options:

- `--direction X Y Z` uses one explicit projection direction.
- `--max-attempts N` controls the deterministic direction search (default 256).
- `--first-generic` returns the first valid generic projection.
- `--prefer-min-crossings` checks all attempts and keeps a diagram with fewer
  crossings; this is the default.
- `--encode-isolated-components` represents a component with no crossings by a
  degenerate R1-style PD crossing instead of omitting it.
- `--epsilon VALUE` sets the geometric tolerance.

Run `build/link-pd-code --help` for the full command-line contract.

## Input Format

```text
component_count
point_count_for_component_0
x y z
...
point_count_for_component_1
x y z
...
```

Each component is closed automatically by connecting its final point to its
first point. Every component needs at least three finite points; zero-length
segments are rejected.

## Algorithm and Correctness

The tool projects the link to a plane, finds proper segment intersections,
orders crossings along every oriented component, assigns arc labels, and emits
each crossing beginning with the incoming under-strand and continuing
clockwise.

Projection directions are deterministic. Non-generic diagrams are rejected,
including endpoint crossings, overlapping projected segments, tied over/under
heights, collapsed segments, and coincident crossings. The intersection path
uses bounding-box and interval pruning plus exact integer-ratio fallback for
numerically brittle segment pairs. Every generated PD code is validated so the
labels are exactly `1..2c` and each occurs twice.

The header-only API is available in `src/link_pd_code.hpp` under the
`cki::link_pd_code` namespace.

## Tests

```sh
python test.py --rebuild --portable
```

The suite covers the CLI, crossingless components, explicit directions,
degenerate projections, Unicode file paths, structural PD validation, and all
22 committed coordinate samples under `test_data/Knot`.

## Provenance

This implementation is the corrected standalone version of the projection
module used by
[`TopologicalKnotIndexer/cpp_knot_indexer`](https://github.com/TopologicalKnotIndexer/cpp_knot_indexer).
The original project license is retained in [LICENSE](LICENSE).
