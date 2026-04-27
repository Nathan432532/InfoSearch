import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { FaThumbsUp, FaThumbsDown } from 'react-icons/fa';
import styles from './JobResultPage.module.css';
import { downloadAsExcel } from '../../../scripts/downloadxl';
import { Pin, CircuitBoard } from 'lucide-react';


const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
// ── Types ─────────────────────────────────────────────────────────────────────

export interface JobResult {
  id: number;
  displayRank?: number;
  bedrijfsnaam: string;
  sector: string;
  locatie: string;
  beschrijving: string;
  waarom: string;
  score: number;
  contactgegevens: string;
  techstack: string[];
  vacatureTitel: string;
  vacatureReferentie?: string;
  urgentie?: string;
  keywords?: string[];
  businessTrigger?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function urgencyClass(urgentie?: string): string {
  if (!urgentie) return '';
  const lower = urgentie.toLowerCase();
  if (lower === 'kritiek') return styles.urgencyCritical;
  if (lower === 'hoog') return styles.urgencyHigh;
  return styles.urgencyMedium;
}

// ── Sub-component: JobCard ────────────────────────────────────────────────────

async function readErrorMessage(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return data?.detail || data?.message || fallback;
  } catch {
    return fallback;
  }
}

async function saveWholeSearch(query: string, filters: Record<string, string>, results: JobResult[]) {
  const response = await fetch(`${API_BASE_URL}/searches/save`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      type: 'job',
      title: `Vacatures: ${query}`,
      filters: Object.keys(filters).length > 0 ? filters : null,
      results,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, 'Opslaan mislukt'));
  }
}

async function saveSingleResult(query: string, filters: Record<string, string>, result: JobResult) {
  const response = await fetch(`${API_BASE_URL}/searches/save-item`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      type: 'job',
      title: `Vacature: ${result.vacatureTitel || result.bedrijfsnaam}`,
      filters: Object.keys(filters).length > 0 ? filters : null,
      result,
      rank: result.displayRank || result.id,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, 'Opslaan mislukt'));
  }
}

function JobCard({
  result,
  searchQuery,
  filters,
  onSaved,
}: {
  result: JobResult;
  searchQuery: string;
  filters: Record<string, string>;
  onSaved: () => void;
}) {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    try {
      setSaving(true);
      await saveSingleResult(searchQuery, filters, result);
      onSaved();
      alert('Vacature opgeslagen.');
    } catch (error) {
      console.error('Fout bij opslaan van vacature:', error);
      alert(error instanceof Error ? error.message : 'Opslaan mislukt.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <li className={styles.result}>
      {/* HEADER */}
      <div className={styles.cardHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.resultIndex}>{result.displayRank ?? result.id}.</span>
          <h2 className={styles.resultName}>{result.bedrijfsnaam}</h2>
          <span className={styles.resultSector}>{result.sector}</span>
        </div>
        <div className={styles.scoreWrapper}>
          <span className={styles.scoreBadge}>{result.score}/10</span>
        </div>
      </div>

      {/* JOB TITLE + URGENCY */}
      <div className={styles.jobTitleRow}>
        <span className={styles.jobTitle}><CircuitBoard /> {result.vacatureTitel}</span>
        {result.urgentie && (
          <span className={`${styles.urgencyBadge} ${urgencyClass(result.urgentie)}`}>
            {result.urgentie}
          </span>
        )}
        {result.vacatureReferentie && (
          <span style={{ fontSize: '0.8em', color: '#aaa' }}>#{result.vacatureReferentie}</span>
        )}
      </div>

      {/* META: locatie */}
      <div className={styles.metaRow}>
        <div className={styles.metaItem}>
          <span className={styles.metaIcon}><Pin /></span>
          <span>{result.locatie}</span>
        </div>
      </div>

      {/* BESCHRIJVING */}
      <p className={styles.resultDescription}>
        {expanded ? result.beschrijving : result.beschrijving.slice(0, 130) + '…'}
      </p>

      {/* EXPANDED */}
      {expanded && (
        <div className={styles.expandedInfo}>
          <div className={styles.infoRow}>
            <strong>Waarom een match:</strong> {result.waarom}
          </div>

          {result.businessTrigger && (
            <div className={styles.infoRow}>
              <strong>Business trigger:</strong> {result.businessTrigger}
            </div>
          )}

          <div className={styles.infoRow}>
            <strong>Tech stack:</strong>
            <div className={styles.techChips}>
              {result.techstack.map((t) => (
                <span key={t} className={styles.techChip}>{t}</span>
              ))}
            </div>
          </div>

          {result.keywords && result.keywords.length > 0 && (
            <div className={styles.infoRow}>
              <strong>Keywords:</strong>
              <div className={styles.keywordChips}>
                {result.keywords.map((k) => (
                  <span key={k} className={styles.keywordChip}>{k}</span>
                ))}
              </div>
            </div>
          )}

          <div className={styles.infoRow}>
            <strong>Contact:</strong> {result.contactgegevens}
          </div>
        </div>
      )}

      {/* FOOTER */}
      <div className={styles.cardFooter}>
        <div className={styles.footerLeft}>
          <button className={styles.btnMore} onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Toon minder' : 'Lees meer'}
          </button>
          <button className={styles.btnSaveItem} onClick={handleSave} disabled={saving}>
            {saving ? 'Bezig...' : 'Bewaar deze vacature'}
          </button>
          {expanded && (
            <button className={styles.btnContact} onClick={() => alert(`Contact: ${result.contactgegevens}`)}>
              ✉ Contacteer
            </button>
          )}
        </div>

        <div className={styles.feedbackButtons}>
          <button
            className={`${styles.thumbUp} ${feedback === 'up' ? styles.active : ''}`}
            onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
            title="Goede match"
          >
            <FaThumbsUp />
          </button>
          <button
            className={`${styles.thumbDown} ${feedback === 'down' ? styles.active : ''}`}
            onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
            title="Geen goede match"
          >
            <FaThumbsDown />
          </button>
        </div>
      </div>
    </li>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function JobResultPage() {
  const [searchParams] = useSearchParams();
  const [results, setResults] = useState<JobResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchedTitle, setSearchedTitle] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [savingWholeSearch, setSavingWholeSearch] = useState(false);
  const location = useLocation();
  const lastRequestKeyRef = useRef<string | null>(null);
  const savedState = (location.state || {}) as {
    isSavedView?: boolean;
    results?: Record<string, unknown>[];
    savedTitle?: string;
    savedQuery?: string;
  };
  const isSavedView = Boolean(savedState?.isSavedView);
  const savedResults = savedState?.results;
  const savedTitle = savedState?.savedTitle || '';
  const savedQuery = savedState?.savedQuery || '';

  const paramsString = searchParams.toString();
  const requestKey = useMemo(
    () => `${paramsString}::saved=${isSavedView ? 1 : 0}::count=${savedResults?.length || 0}::title=${savedTitle}::query=${savedQuery}`,
    [paramsString, isSavedView, savedResults, savedTitle, savedQuery]
  );

  useEffect(() => {
    if (lastRequestKeyRef.current === requestKey) return;
    lastRequestKeyRef.current = requestKey;

    // If coming from saved results, display stored data directly without re-fetching
    if (isSavedView && savedResults && savedResults.length > 0) {
      const mapped: JobResult[] = savedResults.map((r, index) => ({
        id: Number(r.saved_result_id || r.id) || index + 1,
        displayRank: index + 1,
        bedrijfsnaam: (r.bedrijfsnaam as string) || (r.titel as string) || 'Onbekend',
        sector: (r.sector as string) || 'Niet opgegeven',
        locatie: (r.locatie as string) || (r.gemeente as string) || 'Niet opgegeven',
        beschrijving: (r.beschrijving as string) || (r.omschrijving as string) || '',
        waarom: (r.waarom as string) || '',
        score: (r.score as number) || 0,
        contactgegevens: (r.contactgegevens as string) || (r.sollicitatie_email as string) || 'Niet beschikbaar',
        techstack: (r.techstack as string[]) || [],
        vacatureTitel: (r.vacatureTitel as string) || (r.titel as string) || '',
        vacatureReferentie: (r.vacatureReferentie as string) || (r.interne_referentie as string) || undefined,
        urgentie: (r.urgentie as string) || undefined,
        keywords: (r.keywords as string[]) || undefined,
        businessTrigger: (r.businessTrigger as string) || undefined,
      }));
      setResults(mapped);
      setSearchedTitle(savedTitle || savedQuery || '');
      setLoading(false);
      return;
    }

    const query = searchParams.get('query') || '';
    const locatie = searchParams.get('locatie') || '';
    const contractType = searchParams.get('contract_type') || '';
    const sector = searchParams.get('sector') || '';
    const ervaring = searchParams.get('ervaring') || '';

    setSearchedTitle(query);

    if (!query) {
      setError('Voer een zoekopdracht in om vacatures te zoeken.');
      setResults([]);
      setLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const filters: Record<string, string> = {};
        if (locatie) filters.gemeente = locatie;
        if (contractType) filters.contract_type = contractType;
        if (ervaring) filters.ervaring = ervaring;

        const response = await fetch(`${API_BASE_URL}/search`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, filters }),
        });
        if (!response.ok) throw new Error('Failed to fetch results');
        const data = await response.json();

        const mapped: JobResult[] = (data.results || []).map((r: Record<string, unknown>, index: number) => ({
          id: index + 1,
          displayRank: index + 1,
          bedrijfsnaam: (r.bedrijfsnaam as string) || 'Onbekend bedrijf',
          sector: (r.beroep as string) || (sector || 'Niet opgegeven'),
          locatie: [r.gemeente, r.provincie].filter(Boolean).join(', ') || 'Niet opgegeven',
          beschrijving: (r.omschrijving as string) || '',
          waarom: (r.vrije_vereiste as string) || 'Match gebaseerd op vacature-inhoud en filters.',
          score: 0,
          contactgegevens:
            (r.sollicitatie_email as string) ||
            (r.sollicitatie_telefoon as string) ||
            (r.sollicitatie_webformulier as string) ||
            'Niet beschikbaar',
          techstack: [],
          vacatureTitel: (r.titel as string) || 'Vacature',
          vacatureReferentie: (r.interne_referentie as string) || undefined,
          urgentie: (r.status as string) || undefined,
          keywords: [],
          businessTrigger: undefined,
        }));

        setResults(mapped);
        if (mapped.length === 0) {
          setError('Geen vacatures gevonden voor deze zoekopdracht.');
        } else {
          setError(null);
        }
      } catch (err) {
        console.error('Fout bij ophalen vacatures:', err);
        setError('Fout bij het ophalen van vacatures. Controleer of de backend draait.');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestKey, isSavedView, savedResults, savedTitle, savedQuery, searchParams]);

  const activeFilters = useMemo(() => {
    const filters: Record<string, string> = {};
    const locatie = searchParams.get('locatie');
    const contractType = searchParams.get('contract_type');
    const ervaring = searchParams.get('ervaring');
    if (locatie) filters.locatie = locatie;
    if (contractType) filters.contract_type = contractType;
    if (ervaring) filters.ervaring = ervaring;
    return filters;
  }, [searchParams]);

  const handleSaveWholeSearch = async () => {
    try {
      setSavingWholeSearch(true);
      await saveWholeSearch(searchParams.get('query') || searchedTitle, activeFilters, results);
      alert('Zoekopdracht succesvol opgeslagen.');
    } catch (error) {
      console.error('Fout bij opslaan van zoekopdracht:', error);
      alert(error instanceof Error ? error.message : 'Er is een fout opgetreden bij het opslaan.');
    } finally {
      setSavingWholeSearch(false);
    }
  };

  if (loading) return <p style={{ textAlign: 'center', padding: '60px' }}>Laden…</p>;

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>
        Vacature Resultaten{searchedTitle ? ` voor "${searchedTitle}"` : ''}
      </h1>

      {/* ACTION BAR */}
      <div className={styles.actionBar}>
        <button className={styles.btnSave} onClick={handleSaveWholeSearch} disabled={savingWholeSearch || results.length === 0}>
          {savingWholeSearch ? 'Bezig...' : 'Opslaan'}
        </button>
        <button className={styles.btnExport} onClick={() => downloadAsExcel(results, 'vacature-resultaten.xlsx')}>
          Exporteren
        </button>
        <Link to="/keuze">
          <button className={styles.btnNew}>Nieuwe zoekopdracht</button>
        </Link>
      </div>

      {error && <p style={{ color: '#ef4444', padding: '8px 0' }}>{error}</p>}

      {/* COUNT */}
      <p className={styles.resultCount}>{results.length} vacature{results.length !== 1 ? 's' : ''} gevonden</p>

      {/* LIST */}
      <ul className={styles.resultsList}>
        {results.map((result) => (
          <JobCard
            key={`${result.vacatureReferentie || result.id}-${result.bedrijfsnaam}`}
            result={result}
            searchQuery={searchParams.get('query') || searchedTitle}
            filters={activeFilters}
            onSaved={() => undefined}
          />
        ))}
      </ul>
    </main>
  );
}
