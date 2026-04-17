# CyKit

CyKit is a Python library and CLI for acquiring EEG data from supported Emotiv headsets.

## Install

```bash
pip install -e .
```

## Quickstart

```python
from cykit import CyKitClient, Model

with CyKitClient(Model.INSIGHT_CONSUMER) as client:
    for sample in client.stream():
        print(sample.eeg)
        break
```

## What you get

- Root-level public API from `cykit`
- Structured `Sample` objects with float-normalized EEG values
- `discover()` for transport-aware device lookup
- Runtime controls under `client.control`
- CLI compatibility for existing workflows

## Documentation

Detailed guides and API reference live in `docs/` and are built with Sphinx.
