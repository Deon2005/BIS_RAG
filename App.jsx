import { useEffect, useState } from "react";

const RECENT_SEARCHES_KEY = "bis-recent-searches";
const RECENT_MAX = 8;
/** Keeps loading UI visible long enough for errors and fast responses to feel intentional. */
const MIN_LOADING_MS = 1200;

const API_ORIGIN = "http://localhost:8000";

async function probeBackend() {
  async function attempt(path) {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 5000);
    try {
      await fetch(`${API_ORIGIN}${path}`, {
        method: "GET",
        signal: ctrl.signal,
      });
      return true;
    } catch {
      return false;
    } finally {
      clearTimeout(tid);
    }
  }
  return (await attempt("/")) || (await attempt("/docs"));
}

function scorePercent(score) {
  if (score == null || Number.isNaN(Number(score))) return 0;
  const n = Number(score);
  return n <= 1 ? Math.round(n * 100) : Math.round(Math.min(n, 100));
}

function itemKey(item, index) {
  if (item?.id != null && item.id !== "") return String(item.id);
  return `idx-${index}`;
}

function loadRecent() {
  try {
    const raw = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((s) => typeof s === "string") : [];
  } catch {
    return [];
  }
}

function saveRecent(list) {
  try {
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(list));
  } catch {
    /* ignore */
  }
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Wraps query terms in <mark> (same idea as string + replace with HTML, but JSX-safe).
 * Longer words first so "foobar" matches before "foo".
 */
function highlightText(text, query) {
  if (text == null || text === "") return text;
  const str = String(text);
  const words = query
    .split(/\s+/)
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);
  if (words.length === 0) return str;

  const pattern = words.map(escapeRegExp).join("|");
  if (!pattern) return str;

  const regex = new RegExp(`(${pattern})`, "gi");
  const parts = str.split(regex);

  return parts.map((part, i) => {
    if (part === "") return null;
    const isMatch = words.some((w) => w.toLowerCase() === part.toLowerCase());
    if (isMatch) {
      return (
        <mark
          key={i}
          className="rounded-sm bg-amber-200 px-0.5 text-inherit"
        >
          {part}
        </mark>
      );
    }
    return (
      <span key={i} className="contents">
        {part}
      </span>
    );
  });
}

function Spinner() {
  return (
    <svg
      className="size-4 shrink-0 animate-spin"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function ResultSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm ring-1 ring-slate-100">
      <div className="h-5 w-1/3 rounded bg-slate-200" />
      <div className="mt-3 h-4 w-4/5 rounded bg-slate-100" />
      <div className="mt-4 h-2 rounded bg-slate-200" />
      <div className="mt-3 h-3 w-full rounded bg-slate-100" />
      <div className="mt-2 h-3 w-5/6 rounded bg-slate-100" />
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [recent, setRecent] = useState([]);
  const [snippetExpanded, setSnippetExpanded] = useState({});
  /** Query last submitted for search — used for highlights (not live input). */
  const [searchedQuery, setSearchedQuery] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    setRecent(loadRecent());
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setBackendStatus("checking");
      const ok = await probeBackend();
      if (!cancelled) setBackendStatus(ok ? "connected" : "disconnected");
    }
    run();
    const interval = setInterval(run, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const pushRecent = (q) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    const next = [trimmed, ...recent.filter((s) => s !== trimmed)].slice(
      0,
      RECENT_MAX
    );
    setRecent(next);
    saveRecent(next);
  };

  const handleSearch = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    const q = query.trim();
    if (!q || loading) return;

    const startedAt = performance.now();
    setError(null);
    setLoading(true);
    setSearchedQuery(q);

    try {
      const res = await fetch(`${API_ORIGIN}/recommend`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: q }),
      });

      setBackendStatus("connected");

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const msg =
          (typeof data.detail === "string" && data.detail) ||
          (typeof data.message === "string" && data.message) ||
          `Request failed (${res.status})`;
        setError(msg);
        setResults([]);
      } else {
        setResults(data.results || []);
        pushRecent(q);
      }
    } catch (err) {
      console.error(err);
      setBackendStatus("disconnected");
      setError("Could not reach the server. Is the backend running on port 8000?");
      setResults([]);
    } finally {
      const elapsed = performance.now() - startedAt;
      const remaining = Math.max(0, MIN_LOADING_MS - elapsed);
      if (remaining > 0) {
        await new Promise((r) => setTimeout(r, remaining));
      }
      setLoading(false);
      setHasSearched(true);
    }
  };

  const toggleSnippet = (key) => {
    setSnippetExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const showInitialHint = !hasSearched && !loading;
  const showEmpty =
    hasSearched && !loading && results.length === 0 && !error;

  return (
    <div className="min-h-screen bg-stone-50 text-slate-900">
      <div className="mx-auto max-w-2xl space-y-8 px-4 py-10 sm:px-6">
        <header className="space-y-2 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            BIS Standards Recommendation
          </h1>
          <p className="text-sm text-slate-600 sm:text-base">
            Describe a product or use case—we suggest relevant BIS standards and
            why they match.
          </p>
        </header>

        {error && (
          <div
            className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 shadow-sm"
            role="alert"
          >
            <span className="flex-1">{error}</span>
            <button
              type="button"
              className="shrink-0 rounded px-2 py-0.5 text-red-800 underline decoration-red-300 underline-offset-2 hover:bg-red-100 hover:text-red-950 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 focus:ring-offset-red-50"
              onClick={() => setError(null)}
            >
              Dismiss
            </button>
          </div>
        )}

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
            <input
              type="text"
              placeholder="Enter product description…"
              className="min-h-11 flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-300/60"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              aria-label="Product description"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-sky-600 px-5 font-medium text-white shadow-sm hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-stone-50 sm:shrink-0"
            >
              {loading ? (
                <>
                  <Spinner />
                  Searching…
                </>
              ) : (
                "Search"
              )}
            </button>
          </div>

          {recent.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Recent
              </p>
              <div className="flex flex-wrap gap-2">
                {recent.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 shadow-sm hover:border-slate-300 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-stone-50"
                    onClick={() => setQuery(s)}
                  >
                    {s.length > 48 ? `${s.slice(0, 48)}…` : s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>

        {showInitialHint && (
          <p className="text-center text-sm text-slate-500">
            Describe your product to see recommended standards.
          </p>
        )}

        {loading && (
          <div className="space-y-4" aria-busy="true" aria-label="Loading results">
            <ResultSkeleton />
            <ResultSkeleton />
            <ResultSkeleton />
          </div>
        )}

        {showEmpty && (
          <div className="rounded-lg border border-slate-200 bg-white py-8 shadow-sm ring-1 ring-slate-100">
            <div className="space-y-2 text-center">
              <p className="font-medium text-slate-800">No matching standards found</p>
              <p className="text-xs text-slate-500">
                Try adding material type (e.g., cement, steel) or usage context
              </p>
            </div>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="grid gap-4">
            {results.map((item, index) => {
              const key = itemKey(item, index);
              const pct = scorePercent(item.score);
              const snippet = item.snippet ?? "";
              const snippetLong = snippet.length > 200;
              const expanded = snippetExpanded[key];

              return (
                <article
                  key={key}
                  className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-md ring-1 ring-slate-100"
                >
                  {index === 0 && (
                    <span className="mb-2 inline-block rounded bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">
                      Top Match
                    </span>
                  )}

                  <h2 className="text-xl font-bold text-slate-900">
                    {highlightText(item.id, searchedQuery)}
                  </h2>
                  <p className="text-sm text-slate-600">
                    {highlightText(item.title, searchedQuery)}
                  </p>

                  {item.category != null && item.category !== "" && (
                    <p className="mt-1 text-xs font-medium text-sky-600">
                      {highlightText(item.category, searchedQuery)}
                    </p>
                  )}

                  <div className="mt-3 flex items-center gap-3">
                    <div className="h-2 min-w-0 flex-1 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-emerald-500 transition-[width] duration-300"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="shrink-0 text-xs font-medium tabular-nums text-slate-600">
                      {pct}% match
                    </span>
                  </div>

                  {item.rationale && (
                    <p className="mt-3 text-sm leading-relaxed text-slate-800">
                      {highlightText(item.rationale, searchedQuery)}
                    </p>
                  )}

                  {snippet && (
                    <div className="mt-3">
                      <p
                        className={`text-xs leading-relaxed text-slate-500 ${
                          !expanded && snippetLong ? "line-clamp-3" : ""
                        }`}
                      >
                        {highlightText(snippet, searchedQuery)}
                      </p>
                      {snippetLong && (
                        <button
                          type="button"
                          className="mt-1 rounded text-xs font-medium text-sky-700 hover:text-sky-800 focus:outline-none focus:ring-2 focus:ring-sky-400"
                          onClick={() => toggleSnippet(key)}
                        >
                          {expanded ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}

        <footer className="pt-4">
          {backendStatus === "checking" && (
            <p className="text-center text-xs text-slate-500">Checking backend…</p>
          )}
          {backendStatus === "connected" && (
            <p className="text-center text-xs font-medium text-green-600">● Backend connected</p>
          )}
          {backendStatus === "disconnected" && (
            <p className="text-center text-xs font-medium text-amber-600">
              ● Backend unreachable — start the API on port 8000
            </p>
          )}
        </footer>
      </div>
    </div>
  );
}
