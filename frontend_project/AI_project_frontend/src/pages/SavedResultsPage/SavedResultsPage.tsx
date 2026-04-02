import { useEffect, useRef, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import styles from './SavedResultsPage.module.css';
import { Building, CircuitBoard, Folder, Search } from 'lucide-react';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

// ── Types ─────────────────────────────────────────────────────────────────────

interface SavedResult {
  id: number;
  titel: string;
  title?: string;
  query: string;
  datum: string;           // ISO string: "2026-03-09T14:16:00Z"
  type: 'job' | 'company';
  resultUrl?: string;      // optionele link naar de resultaten
  results?: Record<string, unknown>[];
}

type SortOption = 'newest' | 'oldest' | 'alphabetic';

// ── Dummy data ────────────────────────────────────────────────────────────────

const DUMMY_JOBS: SavedResult[] = [
  {
    id: 1,
    titel: 'PLC Specialist Limburg',
    query: 'Siemens S7-1500 Profinet storingstechnieker',
    datum: '2026-03-09T14:49:00Z',
    type: 'job',
    resultUrl: '/results/job',
  },
  {
    id: 3,
    titel: 'Automatisatie Technieker Brussel',
    query: 'Schneider EcoStruxure SCADA onderhoud',
    datum: '2026-02-21T09:30:00Z',
    type: 'job',
    resultUrl: '/results/job',
  },
  {
    id: 5,
    titel: 'Field Service Engineer vacatures',
    query: 'buitendienst elektrotechniek robotica',
    datum: '2026-01-30T08:45:00Z',
    type: 'job',
    resultUrl: '/results/job',
  },
];

const DUMMY_COMPANIES: SavedResult[] = [
  {
    id: 2,
    titel: 'Robotica bedrijven West-Vlaanderen',
    query: 'CAN-bus robotica automatisering Kortrijk',
    datum: '2026-03-09T14:16:00Z',
    type: 'company',
    resultUrl: '/results/company',
  },
  {
    id: 4,
    titel: 'Metaalindustrie partners Genk',
    query: 'Siemens S7 drives metaal elektrische voertuigen',
    datum: '2026-02-15T11:00:00Z',
    type: 'company',
    resultUrl: '/results/company',
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('nl-BE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SavedResultsPage() {
  const navigate = useNavigate();
  const listRef = useRef<HTMLUListElement>(null);
  const [results, setResults] = useState<SavedResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>('newest');

  // ── Fetch ────────────────────────────────────────────────────────────────────

  useEffect(() => {
    const fetchSaved = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/searches/saved`);
        if (!res.ok) throw new Error('Ophalen mislukt');
        const data: SavedResult[] = await res.json();
        setResults(data.map((r: SavedResult) => ({
          ...r,
          titel: r.titel || r.title || r.query,
        })));
      } catch (err) {
        console.error('Fout bij ophalen, dummy data geladen:', err);
        setResults([...DUMMY_JOBS, ...DUMMY_COMPANIES]);
      } finally {
        setLoading(false);
      }
    };
    fetchSaved();
  }, []);

  // animate list in after data loads
  useEffect(() => {
    if (!loading && listRef.current) {
      gsap.fromTo(
        Array.from(listRef.current.children),
        { opacity: 0, x: -20 },
        { opacity: 1, x: 0, duration: 0.38, stagger: 0.06, ease: 'power2.out', clearProps: 'transform' }
      );
    }
  }, [loading]);

  // ── Delete ───────────────────────────────────────────────────────────────────

  const handleDelete = async (id: number, type: 'job' | 'company') => {
    if (!confirm('Weet je zeker dat je dit resultaat wilt verwijderen?')) return;
    try {
      await fetch(`${API_BASE_URL}/searches/saved/${id}`, { method: 'DELETE' });
      setResults((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error('Fout bij verwijderen:', err);
      alert('Verwijderen mislukt.');
    }
  };

  // ── Filter + Sort ─────────────────────────────────────────────────────────────

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase();
    return results
      .filter(
        (r) =>
          r.titel.toLowerCase().includes(q) ||
          formatDate(r.datum).includes(q) ||
          r.query.toLowerCase().includes(q)
      )
      .sort((a, b) => {
        if (sortOption === 'newest') return new Date(b.datum).getTime() - new Date(a.datum).getTime();
        if (sortOption === 'oldest') return new Date(a.datum).getTime() - new Date(b.datum).getTime();
        return a.titel.localeCompare(b.titel, 'nl');
      });
  }, [results, searchQuery, sortOption]);

  // ── Render ────────────────────────────────────────────────────────────────────

  if (loading) return <p className={styles.statusMessage}>Laden…</p>;

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>Opgeslagen zoekresultaten</h1>

      {/* CONTROL PANEL */}
      <div className={styles.controlPanel}>
        <div className={styles.searchBox}>
          <input
            type="text"
            placeholder="Zoek op titel, query of datum..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className={styles.searchIcon}><Search/></span>
        </div>

        <div className={styles.sortControls}>
          <label className={styles.sortLabel}>Sorteren op:</label>
          <select
            className={styles.sortSelect}
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value as SortOption)}
          >
            <option value="newest">Datum: van nieuw naar oud</option>
            <option value="oldest">Datum: van oud naar nieuw</option>
            <option value="alphabetic">Titel: van A naar Z</option>
          </select>
        </div>
      </div>

      {/* COUNT */}
      <p className={styles.resultCount}>
        {filtered.length} opgeslagen resultaat{filtered.length !== 1 ? 'en' : ''}
      </p>

      {/* LIST */}
      {filtered.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}><Folder></Folder></div>
          <p className={styles.emptyText}>Geen opgeslagen resultaten gevonden.</p>
          <p className={styles.emptySubText}>
            Probeer een andere zoekterm of sla eerst een zoekopdracht op.
          </p>
        </div>
      ) : (
        <ul className={styles.list} ref={listRef}>
          {filtered.map((result) => (
            <li key={result.id} className={styles.savedItem}>
              <div
                className={styles.itemLink}
                onClick={() => navigate(`/results/${result.type}`, {
                  state: {
                    isSavedView: true,
                    results: result.results || [],
                    savedTitle: result.titel,
                    savedQuery: result.query,
                  },
                })}
                style={{ cursor: 'pointer' }}
              >
                <span
                  className={`${styles.typeBadge} ${
                    result.type === 'job' ? styles.typeBadgeJob : styles.typeBadgeCompany
                  }`}
                >
                  {result.type === 'job' ? <CircuitBoard/> : <Building/>}
                </span>

                <div className={styles.itemContent}>
                  <span className={styles.itemTitle}>{result.titel}</span>
                  <span className={styles.itemQuery}>"{result.query}"</span>
                </div>

                <span className={styles.itemDate}>{formatDate(result.datum)}</span>
              </div>

              <button
                className={styles.deleteBtn}
                onClick={() => handleDelete(result.id, result.type)}
                title="Verwijder"
              >
                🗑
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
