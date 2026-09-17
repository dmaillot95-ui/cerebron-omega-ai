# FARM-46 — Global Video Research

Mission: search, index and rank publicly accessible video sources worldwide for research use, while preserving source URLs, publication metadata and provenance.

Rules:
- REALITY > COHERENCE
- CLAIM <= EVIDENCE
- VIDEO RESULT != VALIDATED CLAIM
- Never treat a video as proof by itself.
- Prefer original channels, institutional sources, conference recordings, lectures and primary demonstrations.
- Deduplicate mirrors/reuploads.
- Record language, country/region when reliably known, date, source platform, title and URL.
- Respect platform terms, robots rules, rate limits and authentication requirements.

Initial source classes:
- YouTube public search/results
- PeerTube public instances
- Internet Archive moving-image collections
- Vimeo public pages when searchable
- institutional conference/video portals
- university lecture portals

Output packet:
- query
- timestamp
- source platform
- title
- URL
- publisher/channel
- publication date when available
- language when available
- evidence class: PRIMARY / SECONDARY / COMMENTARY / UNKNOWN
- duplication hash
- relevance score
- caveats

This farm is initially hosted inside the central repository. A standalone repository can be created later if repository-creation access is added to the connector.
