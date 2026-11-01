# Observability & Instrumentation Checklist

Companion reference for `observability-and-instrumentation/SKILL.md`.

## 1. Structured Logging
- [ ] Logs emit structured JSON with `timestamp`, `level`, `requestId`/`traceId`, `service`, and contextual metadata.
- [ ] Zero PII, passwords, bearer tokens, or raw session cookies are written to log sinks.
- [ ] Expected 4xx client validation errors log at `warn`/`info`, while unhandled 5xx faults log at `error` with stack traces.

## 2. Health Probes & Metrics
- [ ] `/api/health` (or `/healthz`) verifies critical downstream dependencies (DB ping, Redis readiness) with strict timeouts (`≤2s`) and returns `"status": "ok"`.
- [ ] Latency histograms track `p50`, `p95`, and `p99` alongside error rates and saturation (DB pool utilization, queue depth).

## 3. APM & Client Telemetry Hygiene
- [ ] Browser APM SDKs (Sentry, Clarity, GA4) load asynchronously outside the critical FCP/LCP window.
- [ ] Hidden-tab web vitals (`document.visibilityState === 'hidden'`) and runaway background transactions (`>28s`) are filtered out in `beforeSendTransaction`.
