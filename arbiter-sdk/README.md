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

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:842f76d4aebb431fea3c920fba2d288f87fe015a2ad6366b4e2d87325a3d7c02 -->

The SDK sends each event once. It does not retry a send that failed or that the
API rejected. A failed request may have an unknown outcome: the API may have
saved the run even if its response was lost.

<!-- /coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:0d73e128b6638fdf44a3e0ca5819c5fcc7518c224fcd493fe1839e2db0ad5d29 -->

Each Arbiter instance has its own dispatcher. When your process exits normally,
the SDK waits up to five seconds per dispatcher to send what is left in its
queue. This is not a process-wide five-second limit. Events still in the queue
after that wait are lost. Events whose sends are still in progress may also be
lost on normal process exit, even if already removed from the queue. A process
that another program kills can leave the queue unsent.

<!-- /coderabbit-ai-generated:v1 -->

Read the root README for the full Arbiter quickstart.
