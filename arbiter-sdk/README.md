# Arbiter SDK

The SDK reports your pipeline runs to Arbiter from Python code. You put one
decorator on a function. When your code calls that function, the SDK sends one
run event to the API.

## Install

Run this command from the repository root:

```sh
pip install -e ./arbiter-sdk
```

## Usage

```python
from arbiter import Arbiter

arb = Arbiter(api_key="arb_test_xxx", pipeline="my_pipeline")

@arb.monitor
def my_function():
    ...
```

`Arbiter` takes three arguments: `api_key`, `pipeline` and `api_url`. The
default `api_url` is `http://localhost:8000`. The key needs the
`collector:write` scope.

## What the SDK does

The decorator starts one background thread. Your function puts its run event in
a queue and returns; the thread sends the event to the API. A slow or stopped
API does not stop your code.

That queue holds 1000 events. When the queue is full, the SDK drops the new
event and writes `arbiter_queue_full` to the log. Watch that message when you
run many jobs on one host.

The SDK sends each event once. It does not retry a send that failed or that the
API rejected. Such an event is lost.

When your process exits normally, the SDK waits up to five seconds to send what
is left in the queue. Events still in the queue after that wait are lost. A
process that another program kills can leave the queue unsent.

Read the root README for the full Arbiter quickstart.
