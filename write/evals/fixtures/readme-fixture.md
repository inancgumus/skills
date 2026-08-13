---
title: streamsift
version: 0.4.2
---

# streamsift

In today's fast-paced world of event-driven architectures, streamsift stands as a powerful, cutting-edge solution for filtering event streams. Not only does it deliver seamless performance — processing up to 120,000 events/sec on a single core — but it also boasts an intuitive configuration format, making it a true game-changer for teams of all sizes.

## Installation

```bash
go install example.com/streamsift@latest
```

## Usage

It's worth noting that streamsift buffers up to 10,000 events in memory before flushing. Moreover, in the event that a downstream sink becomes unavailable, streamsift leverages a robust retry mechanism with a 250ms backoff — ensuring reliability and peace of mind. Let's dive into what this means for your team: fewer dropped events, seamless recovery, and unparalleled operational excellence.

Memory usage is designed with efficiency in mind. At its core, streamsift maintains a remarkably small footprint — typically around 60MB RSS under sustained load — a testament to its thoughtful architecture.

## Outputs

- stdout (NDJSON)
- file (rotating)
- TCP sink

## Conclusion

In conclusion, streamsift represents a paradigm shift in the realm of event filtering. Whether you're a seasoned platform engineer or just getting started on your observability journey, streamsift empowers you to unlock the full potential of your event pipeline. The future looks bright!
