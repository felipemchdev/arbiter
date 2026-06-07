# Arbiter SDK

Python instrumentation library for reporting pipeline runs to Arbiter.

## Install

```sh
pip install -e ./arbiter-sdk
```

## Usage

```python
from arbiter import Arbiter

arb = Arbiter(api_key="arb_xxx", pipeline="my_pipeline")

@arb.monitor
def my_function():
    ...
```

See the root README for the full Arbiter quickstart.
