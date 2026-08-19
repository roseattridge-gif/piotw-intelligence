# Evidence Engine 0.3.1 blinded source-pack repair

Document `ee03-alb-0000915913-24-000156` in the original pack was a four-page Form 8-K wrapper that referred to Exhibit 99.1 but omitted the exhibit. The replacement appends the official SEC Exhibit 99.1 and is 24 pages.

- Original SHA-256: `050f39c61a73b5bc5fa136b294d3752cfabe074226c5a3672017b138e94dca19`
- Repaired SHA-256: `a9ee338e3f4bfb4c8931bc8d435dc2d3cbabd3c057e1fee36a74b84c0cf2d839`
- Reason: source completeness defect; the reviewer otherwise could not see the furnished results.
- Original pack: preserved unchanged.
- Formal annotation status: the formal gold observation and event files remain blank and retain their prior hashes.
- Blinding: the repaired file contains only the issuer/SEC source, not PIOTW or AI answers.

The replacement belongs only in the versioned `Evidence Engine 0.3 - Blinded Reviewer Pack v2`. The original pack must not be overwritten.
