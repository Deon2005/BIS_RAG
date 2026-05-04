import { useEffect, useState } from "react";
import { Search, Database, Layers, ArrowRight, FileText, CheckCircle2, ChevronRight, BookOpen } from "lucide-react";

const RECENT_MAX = 4;
const MIN_LOADING_MS = 1000;
const API_ORIGIN = "http://localhost:8000";

async function probeBackend() {
  try {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 3000);
    await fetch(`${API_ORIGIN}/health`, { method: "GET", signal: ctrl.signal });
    clearTimeout(tid);
    return true;
  } catch {
    return false;
  }
}

function scorePercent(score) {
  if (score == null || Number.isNaN(Number(score))) return 0;
  const n = Number(score);
  return n <= 1 ? Math.round(n * 100) : Math.round(Math.min(n, 100));
}

function highlightText(text, query) {
  if (!text) return text;
  const str = String(text);
  const words = query.split(/\s+/).filter(Boolean).sort((a, b) => b.length - a.length);
  if (words.length === 0) return str;

  const pattern = words.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  if (!pattern) return str;

  const regex = new RegExp(`(${pattern})`, "gi");
  return str.split(regex).map((part, i) => {
    if (!part) return null;
    const isMatch = words.some((w) => w.toLowerCase() === part.toLowerCase());
    if (isMatch) {
      return (
        <span key={i} className="text-[#00f0ff] font-semibold">
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function Loader() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative flex h-16 w-16 items-center justify-center">
        <div className="absolute h-full w-full animate-[spin_3s_linear_infinite] rounded-full border-b-2 border-l-2 border-t-2 border-[#333]"></div>
        <div className="absolute h-10 w-10 animate-[spin_2s_linear_infinite_reverse] rounded-full border-b-2 border-r-2 border-t-2 border-[#666]"></div>
        <div className="h-4 w-4 animate-pulse rounded-full bg-[#fff]"></div>
      </div>
      <p className="mt-6 text-sm font-medium tracking-widest text-[#888] uppercase">Querying Datastore</p>
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [recent, setRecent] = useState(["fly ash bricks", "portland cement", "reinforcement steel"]);
  const [expandedId, setExpandedId] = useState(null);
  const [searchedQuery, setSearchedQuery] = useState("");
  const [status, setStatus] = useState("connected");

  const handleSearch = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    const q = query.trim();
    if (!q || loading) return;

    const startedAt = performance.now();
    setError(null);
    setLoading(true);
    setSearchedQuery(q);
    setExpandedId(null);

    try {
      const res = await fetch(`${API_ORIGIN}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || `Connection error (${res.status})`);
        setResults([]);
      } else {
        setResults(data.results || []);
        if (!recent.includes(q)) setRecent([q, ...recent].slice(0, RECENT_MAX));
      }
    } catch (err) {
      setError("Unable to connect to the compliance index.");
      setResults([]);
    } finally {
      const remaining = Math.max(0, MIN_LOADING_MS - (performance.now() - startedAt));
      if (remaining > 0) await new Promise(r => setTimeout(r, remaining));
      setLoading(false);
      setHasSearched(true);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#ececec] font-sans selection:bg-[#fff] selection:text-[#000]">
      {/* Dynamic Background Noise */}
      <div className="pointer-events-none fixed inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }}></div>
      
      {/* Top Navbar */}
      <nav className="relative z-10 flex items-center justify-between border-b border-[#222] bg-[#0a0a0a]/80 px-8 py-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-white text-black">
            <Layers className="h-4 w-4" strokeWidth={2.5} />
          </div>
          <span className="text-sm font-semibold tracking-wide">BUREAU COMPLIANCE</span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${status === 'connected' ? 'bg-[#00ff9d] shadow-[0_0_8px_#00ff9d]' : 'bg-[#ff3366]'}`} />
          <span className="text-xs font-mono text-[#888]">{status === 'connected' ? 'INDEX_ONLINE' : 'SYS_ERR'}</span>
        </div>
      </nav>

      {/* Main Layout: Split Screen on Desktop */}
      <div className="relative z-10 flex min-h-[calc(100vh-65px)] flex-col lg:flex-row">
        
        {/* LEFT PANE: Search Interface */}
        <div className="flex w-full flex-col justify-center border-r border-[#222] bg-[#0a0a0a] p-8 lg:w-2/5 xl:p-16">
          <div className="max-w-md w-full mx-auto">
            <h1 className="mb-2 text-4xl font-normal tracking-tight text-white sm:text-5xl">
              Specification Lookup.
            </h1>
            <p className="mb-10 text-sm leading-relaxed text-[#888]">
              Cross-reference material properties against the official structural repository. Enter parameters to begin.
            </p>

            <form onSubmit={handleSearch} className="relative group">
              {/* Animated Border Glow */}
              <div className="absolute -inset-0.5 rounded-xl bg-gradient-to-r from-[#333] to-[#555] opacity-20 blur transition duration-500 group-hover:opacity-60"></div>
              
              <div className="relative flex items-center rounded-xl border border-[#333] bg-[#0f0f0f] transition-all hover:border-[#666] focus-within:border-[#fff] focus-within:ring-1 focus-within:ring-[#fff]">
                <input
                  type="text"
                  placeholder="Material specs..."
                  className="w-full bg-transparent px-5 py-4 text-base placeholder:text-[#555] focus:outline-none"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={loading}
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="mr-2 flex h-10 w-10 items-center justify-center rounded-lg bg-[#fff] text-black transition-transform hover:scale-105 disabled:opacity-30 disabled:hover:scale-100"
                >
                  <ArrowRight className="h-4 w-4" strokeWidth={3} />
                </button>
              </div>
            </form>

            <div className="mt-8">
              <span className="mb-4 block text-[10px] font-bold uppercase tracking-widest text-[#555]">Query Log</span>
              <div className="flex flex-col gap-2">
                {recent.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => { setQuery(s); handleSearch({ preventDefault: () => {} }); }}
                    className="flex items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-[#999] transition-colors hover:bg-[#1a1a1a] hover:text-white"
                  >
                    <Search className="h-3 w-3 opacity-50" />
                    <span className="truncate">{s}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANE: Results Area */}
        <div className="flex w-full flex-col bg-[#050505] lg:w-3/5">
          <div className="h-full overflow-y-auto p-8 xl:p-16 scrollbar-thin scrollbar-thumb-[#333]">
            
            {error && (
              <div className="mb-6 rounded-lg border border-[#ff3366]/30 bg-[#ff3366]/10 p-5 text-sm text-[#ff3366]">
                ERROR_CODE: {error}
              </div>
            )}

            {!hasSearched && !loading && !error && (
              <div className="flex h-full flex-col items-center justify-center text-center opacity-30">
                <Database className="mb-4 h-12 w-12" strokeWidth={1} />
                <p className="font-mono text-sm uppercase tracking-widest">Awaiting Input</p>
              </div>
            )}

            {loading && <Loader />}

            {hasSearched && !loading && results.length === 0 && !error && (
              <div className="flex h-full flex-col items-center justify-center text-center opacity-50">
                <FileText className="mb-4 h-12 w-12" strokeWidth={1} />
                <p className="font-mono text-sm uppercase tracking-widest">0 Records Matched</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <div className="flex flex-col gap-4">
                <div className="mb-4 flex items-center justify-between border-b border-[#222] pb-4">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#888]">
                    Retrieved Entities ({results.length})
                  </span>
                  <span className="font-mono text-xs text-[#555]">SORT: RRF_SCORE_DESC</span>
                </div>

                {results.map((item, index) => {
                  const pct = scorePercent(item.score);
                  const isExpanded = expandedId === item.id;

                  return (
                    <div 
                      key={item.id} 
                      className={`group relative overflow-hidden rounded-xl border bg-[#0a0a0a] transition-all duration-300 ${
                        index === 0 ? "border-[#444]" : "border-[#1a1a1a]"
                      } hover:border-[#666]`}
                    >
                      {/* Interactive Header */}
                      <div 
                        className="flex cursor-pointer items-start justify-between p-6"
                        onClick={() => setExpandedId(isExpanded ? null : item.id)}
                      >
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm font-bold text-white">
                              {highlightText(item.id, searchedQuery)}
                            </span>
                            {item.category && (
                              <span className="rounded bg-[#1a1a1a] px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-[#888]">
                                {item.category}
                              </span>
                            )}
                            {index === 0 && (
                              <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-[#00ff9d]">
                                <CheckCircle2 className="h-3 w-3" /> Optimal
                              </span>
                            )}
                          </div>
                          <h3 className="text-base font-medium text-[#ccc] group-hover:text-white transition-colors">
                            {highlightText(item.title, searchedQuery)}
                          </h3>
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          <span className="font-mono text-xs text-[#666]">v-{pct}</span>
                          <div className="h-1 w-16 overflow-hidden rounded-full bg-[#222]">
                            <div className="h-full bg-white transition-all duration-1000" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      </div>

                      {/* Expandable Details Pane */}
                      <div className={`overflow-hidden transition-all duration-500 ease-in-out ${isExpanded ? 'max-h-[800px] border-t border-[#222] opacity-100' : 'max-h-0 opacity-0'}`}>
                        <div className="bg-[#111] p-6">
                          
                          {item.rationale && (
                            <div className="mb-6">
                              <h4 className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#666]">
                                <BookOpen className="h-3 w-3" /> Synthesis
                              </h4>
                              <p className="text-sm leading-relaxed text-[#aaa]">
                                {highlightText(item.rationale, searchedQuery)}
                              </p>
                            </div>
                          )}

                          {item.snippet && (
                            <div>
                              <h4 className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#666]">
                                <FileText className="h-3 w-3" /> Raw Context
                              </h4>
                              <div className="rounded-lg border border-[#222] bg-[#050505] p-4">
                                <p className="font-mono text-xs leading-loose text-[#888]">
                                  {highlightText(item.snippet, searchedQuery)}
                                </p>
                              </div>
                            </div>
                          )}
                          
                          <div className="mt-6 flex justify-end">
                             <button className="flex items-center gap-2 text-xs font-medium text-white hover:underline underline-offset-4">
                               Open Full Document <ChevronRight className="h-3 w-3" />
                             </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
