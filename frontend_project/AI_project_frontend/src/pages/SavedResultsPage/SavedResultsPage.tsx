import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import styles from './SavedResultsPage.module.css';
import { Building, CircuitBoard, Folder, Search } from 'lucide-react';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

type SavedKind = 'job' | 'company';
type ViewMode = 'searches' | 'results';
type GroupedSaved<T> = Record<SavedKind, T[]>;

interface SavedSearch {
  id: number;
  titel: string;
  title?: string;
  query: string;
  datum: string;
  type: SavedKind;
  resultUrl?: string;
  results?: Record<string, unknown>[];
}

interface SavedResultItem {
  id: number;
  search_id: number;
  type: SavedKind;
  title: string;
  query: string;
  datum: string;
  rank?: number;
  score?: number | null;
  result: Record<string, unknown>;
}

interface SavedPayload {
  searches: GroupedSaved<SavedSearch>;
  results: GroupedSaved<SavedResultItem>;
}

type SortOption = 'newest' | 'oldest' | 'alphabetic';

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('nl-BE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function typeLabel(type: SavedKind): string {
  return type === 'job' ? 'Vacatures' : 'Bedrijven';
}

export default function SavedResultsPage() {
  const navigate = useNavigate();
  const listRef = useRef<HTMLDivElement>(null);
  const [payload, setPayload] = useState<SavedPayload>({
    searches: { company: [], job: [] },
    results: { company: [], job: [] },
  });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>('newest');
  const [viewMode, setViewMode] = useState<ViewMode>('searches');

  useEffect(() => {
    const fetchSaved = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/searches/saved`);
        if (!res.ok) throw new Error('Ophalen mislukt');
        const data: SavedPayload = await res.json();

        setPayload({
          searches: {
            company: (data.searches?.company || []).map((item) => ({
              ...item,
              titel: item.titel || item.title || item.query,
            })),
            job: (data.searches?.job || []).map((item) => ({
              ...item,
              titel: item.titel || item.title || item.query,
            })),
          },
          results: {
            company: data.results?.company || [],
            job: data.results?.job || [],
          },
        });
      } catch (err) {
        console.error('Fout bij ophalen opgeslagen data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSaved();
  }, []);

  useEffect(() => {
    if (!loading && listRef.current) {
      gsap.fromTo(
        Array.from(listRef.current.querySelectorAll(`.${styles.savedItem}`)),
        { opacity: 0, x: -20 },
        { opacity: 1, x: 0, duration: 0.38, stagger: 0.04, ease: 'power2.out', clearProps: 'transform' }
      );
    }
  }, [loading, payload, viewMode, searchQuery, sortOption]);

  const handleDeleteSearch = async (id: number, type: SavedKind) => {
    if (!confirm('Weet je zeker dat je deze zoekopdracht wilt verwijderen?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/searches/saved/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Verwijderen mislukt');

      setPayload((prev) => ({
        ...prev,
        searches: {
          ...prev.searches,
          [type]: prev.searches[type].filter((item) => item.id !== id),
        },
        results: {
          company: prev.results.company.filter((item) => item.search_id !== id),
          job: prev.results.job.filter((item) => item.search_id !== id),
        },
      }));
    } catch (err) {
      console.error('Fout bij verwijderen zoekopdracht:', err);
      alert('Verwijderen mislukt.');
    }
  };

  const handleDeleteResult = async (id: number, type: SavedKind) => {
    if (!confirm('Weet je zeker dat je dit opgeslagen resultaat wilt verwijderen?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/searches/saved-item/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Verwijderen mislukt');

      setPayload((prev) => ({
        ...prev,
        results: {
          ...prev.results,
          [type]: prev.results[type].filter((item) => item.id !== id),
        },
      }));
    } catch (err) {
      console.error('Fout bij verwijderen resultaat:', err);
      alert('Verwijderen mislukt.');
    }
  };

  const filteredSearches = useMemo(() => {
    const filterItems = (items: SavedSearch[]) => {
      const q = searchQuery.toLowerCase();
      return items
        .filter(
          (item) =>
            item.titel.toLowerCase().includes(q) ||
            item.query.toLowerCase().includes(q) ||
            formatDate(item.datum).includes(q)
        )
        .sort((a, b) => {
          if (sortOption === 'newest') return new Date(b.datum).getTime() - new Date(a.datum).getTime();
          if (sortOption === 'oldest') return new Date(a.datum).getTime() - new Date(b.datum).getTime();
          return a.titel.localeCompare(b.titel, 'nl');
        });
    };

    return {
      company: filterItems(payload.searches.company),
      job: filterItems(payload.searches.job),
    };
  }, [payload.searches, searchQuery, sortOption]);

  const filteredResults = useMemo(() => {
    const filterItems = (items: SavedResultItem[]) => {
      const q = searchQuery.toLowerCase();
      return items
        .filter((item) => {
          const title = String(item.result.bedrijfsnaam || item.result.vacatureTitel || item.result.titel || item.title || '').toLowerCase();
          return (
            title.includes(q) ||
            item.query.toLowerCase().includes(q) ||
            formatDate(item.datum).includes(q)
          );
        })
        .sort((a, b) => {
          if (sortOption === 'newest') return new Date(b.datum).getTime() - new Date(a.datum).getTime();
          if (sortOption === 'oldest') return new Date(a.datum).getTime() - new Date(b.datum).getTime();
          const aTitle = String(a.result.bedrijfsnaam || a.result.vacatureTitel || a.result.titel || a.title || '');
          const bTitle = String(b.result.bedrijfsnaam || b.result.vacatureTitel || b.result.titel || b.title || '');
          return aTitle.localeCompare(bTitle, 'nl');
        });
    };

    return {
      company: filterItems(payload.results.company),
      job: filterItems(payload.results.job),
    };
  }, [payload.results, searchQuery, sortOption]);

  const totalVisible = viewMode === 'searches'
    ? filteredSearches.company.length + filteredSearches.job.length
    : filteredResults.company.length + filteredResults.job.length;

  if (loading) return <p className={styles.statusMessage}>Laden…</p>;

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>Opgeslagen resultaten</h1>

      <div className={styles.controlPanel}>
        <div className={styles.searchBox}>
          <input
            type="text"
            placeholder="Zoek op titel, query of datum..."
            className={styles.searchInput}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className={styles.searchIcon}><Search /></span>
        </div>

        <div className={styles.toolbarRow}>
          <div className={styles.segmentedControl}>
            <button
              className={`${styles.segmentButton} ${viewMode === 'searches' ? styles.segmentButtonActive : ''}`}
              onClick={() => setViewMode('searches')}
            >
              Hele zoekopdrachten
            </button>
            <button
              className={`${styles.segmentButton} ${viewMode === 'results' ? styles.segmentButtonActive : ''}`}
              onClick={() => setViewMode('results')}
            >
              Individuele resultaten
            </button>
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
      </div>

      <p className={styles.resultCount}>
        {totalVisible} opgeslagen {viewMode === 'searches' ? 'zoekopdracht' : 'resultaat'}{totalVisible !== 1 ? 'en' : ''}
      </p>

      <div className={styles.groupContainer} ref={listRef}>
        {(['job', 'company'] as SavedKind[]).map((type) => {
          const items = viewMode === 'searches' ? filteredSearches[type] : filteredResults[type];
          return (
            <section key={`${viewMode}-${type}`} className={styles.groupSection}>
              <div className={styles.groupHeader}>
                <span className={`${styles.typeBadge} ${type === 'job' ? styles.typeBadgeJob : styles.typeBadgeCompany}`}>
                  {type === 'job' ? <CircuitBoard /> : <Building />}
                </span>
                <div>
                  <h2 className={styles.groupTitle}>{typeLabel(type)}</h2>
                  <p className={styles.groupMeta}>{items.length} item{items.length !== 1 ? 's' : ''}</p>
                </div>
              </div>

              {items.length === 0 ? (
                <div className={styles.emptyStateSmall}>Geen opgeslagen {viewMode === 'searches' ? 'zoekopdrachten' : 'resultaten'}.</div>
              ) : viewMode === 'searches' ? (
                <ul className={styles.list}>
                  {(items as SavedSearch[]).map((item) => (
                    <li key={item.id} className={styles.savedItem}>
                      <div
                        className={styles.itemLink}
                        onClick={() => navigate(`/results/${item.type}`, {
                          state: {
                            isSavedView: true,
                            results: item.results || [],
                            savedTitle: item.titel,
                            savedQuery: item.query,
                          },
                        })}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className={styles.itemContent}>
                          <span className={styles.itemTitle}>{item.titel}</span>
                          <span className={styles.itemQuery}>"{item.query}"</span>
                        </div>
                        <span className={styles.itemDate}>{formatDate(item.datum)}</span>
                      </div>

                      <button
                        className={styles.deleteBtn}
                        onClick={() => handleDeleteSearch(item.id, item.type)}
                        title="Verwijder"
                      >
                        🗑
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <ul className={styles.list}>
                  {(items as SavedResultItem[]).map((item) => {
                    const resultTitle = String(item.result.bedrijfsnaam || item.result.vacatureTitel || item.result.titel || item.title || 'Opgeslagen resultaat');
                    const score = item.score ?? item.result.score;
                    return (
                      <li key={item.id} className={styles.savedItem}>
                        <div
                          className={styles.itemLink}
                          onClick={() => navigate(`/results/${item.type}`, {
                            state: {
                              isSavedView: true,
                              results: [item.result],
                              savedTitle: resultTitle,
                              savedQuery: item.query,
                            },
                          })}
                          style={{ cursor: 'pointer' }}
                        >
                          <div className={styles.itemContent}>
                            <span className={styles.itemTitle}>{resultTitle}</span>
                            <span className={styles.itemQuery}>"{item.query}"</span>
                          </div>
                          <div className={styles.itemMetaBlock}>
                            {typeof score === 'number' ? <span className={styles.scorePill}>{score}/10</span> : null}
                            <span className={styles.itemDate}>{formatDate(item.datum)}</span>
                          </div>
                        </div>

                        <button
                          className={styles.deleteBtn}
                          onClick={() => handleDeleteResult(item.id, item.type)}
                          title="Verwijder"
                        >
                          🗑
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          );
        })}
      </div>

      {totalVisible === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}><Folder /></div>
          <p className={styles.emptyText}>Geen opgeslagen gegevens gevonden.</p>
          <p className={styles.emptySubText}>Sla eerst een zoekopdracht of individueel resultaat op.</p>
        </div>
      )}
    </main>
  );
}
