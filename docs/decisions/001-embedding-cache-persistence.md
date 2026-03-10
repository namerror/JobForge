### Context
We cache embeddings for role text and normalized skill text to reduce repeated embedding API calls and improve latency. The cache must be deterministic, safe on crashes, and compatible with the baseline scorer. The current approach was implemented as a write-through disk cache backed by JSON files.

### Decision
Adopt a write-through, JSON-on-disk embedding cache with atomic file replacement and metadata validation.

Key points:
- Store embeddings on disk as JSON (two files: role and skill).
- Write-through persistence: every cache store immediately writes to disk.
- Atomic writes using a temporary file + `os.replace` to avoid corruption.
- Cache keys are raw text (role text and normalized skill text).
- Cache is single-process only (no file locking).
- Include model metadata (model name and embedding dimensions) in the file payload; reject mismatches.
- Keep backwards compatibility with the legacy raw-dict format (treated as data on load).

### Read/Write Process
**Read:**
1. On `EmbeddingCache` init, attempt to load role and skill cache JSON files.
2. If file missing, use empty dict and log a warning.
3. If payload has metadata:
   - Validate `model` and `dimensions` against current settings.
   - If mismatch, log warning and ignore file (empty cache).
4. If payload is legacy raw dict, accept as data.

**Write (write-through):**
1. On `cache_store(...)`, update in-memory dict.
2. Serialize payload to a temp file in the same directory.
3. Atomically replace the target JSON file.

### Data Format
Two JSON files stored under `app/data/embeddings/{model}/`:
- `role_cache.json`
- `skill_cache.json`

### Payload Format
```json
{
  "version": 1,
  "model": "text-embedding-3-small",
  "dimensions": 1536,
  "data": {
    "raw text": [0.1, 0.2, ...]
  }
}
```

Notes:
- `model` and `dimensions` must match current settings.
- `dimensions` may be `null` if not configured.
- `data` maps raw text to float vectors.

### Storage Method
Disk-backed JSON with atomic writes. No in-memory LRU or eviction at this stage; the in-memory dict mirrors the disk content for the process lifetime.

### Assumptions (Architecture POV)
- Single-process writer: no concurrent writes across processes.
- Raw text keys are acceptable for readability and debugging.
- JSON file sizes are manageable within current workload.
- Cache integrity is preferred over maximum throughput.
- Backward compatibility with legacy cache format is required.

### Consequences
**Pros:**
- Simple, inspectable storage format.
- Crash-safe writes via atomic replacement.
- Deterministic persistence behavior (no reliance on `__del__`).
- Clear model/dimension validation to prevent mixed embeddings.

**Cons:**
- Write-through can be I/O heavy under large batch workloads.
- JSON size can grow without bounds; no eviction policy.
- No multi-process safety (no locking or merge strategy).

### Alternatives Considered
- `__del__` or `__exit__` persistence: rejected due to unreliable shutdown behavior.
- In-memory only: rejected due to loss on crash/restart.
- SQLite or LMDB: deferred to keep dependency surface minimal.

### Future Considerations
**Hybrid in-memory + disk cache**
- Approach: keep an in-memory LRU and periodically flush a write-behind log or checkpoint.
- Pros:
  - Lower write overhead.
  - Faster lookups for hot keys.
  - Allows bounded memory use with eviction.
- Cons:
  - Risk of data loss on crash (write-behind).
  - Complexity: eviction + sync logic + durability guarantees.

**Alternative storage backends**
1. **SQLite**
   - Pros: atomic transactions, built-in locking, easy queries, single-file storage.
   - Cons: extra dependency, potential perf overhead vs pure dict.
2. **LMDB**
   - Pros: very fast key-value storage, good for large data, ACID semantics.
   - Cons: external dependency, more operational complexity.
3. **Redis or external cache**
   - Pros: shared cache across workers/hosts, eviction policies, persistence options.
   - Cons: operational overhead, network latency, external service dependency.
4. **Parquet or NPZ files**
   - Pros: efficient numeric storage.
   - Cons: harder key-based lookups; still need an index.

If/when multi-process usage or cache size grows materially, prefer SQLite or LMDB as the next step due to durability and concurrency support.
