import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FaThumbsUp, FaThumbsDown } from 'react-icons/fa';
import styles from './CompanyResultPage.module.css';
import { downloadAsExcel } from '../../../scripts/downloadxl';
import { Pin, Building } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CompanyResult {
  id: number;
  bedrijfsnaam: string;
  sector: string;
  locatie: string;
  beschrijving: string;
  waarom: string;
  score: number;
  contactgegevens: string;
  techstack: string[];
  machinepark?: string[];
  businessTrigger?: string;
  matchKwaliteit?: 'Sterke match' | 'Goede match' | 'Gedeeltelijke match';
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function matchClass(kwaliteit?: string): string {
  if (!kwaliteit) return '';
  if (kwaliteit === 'Sterke match') return styles.matchStrong;
  if (kwaliteit === 'Goede match') return styles.matchGood;
  return styles.matchPartial;
}

// ── Sub-component: CompanyCard ────────────────────────────────────────────────

function CompanyCard({ result }: { result: CompanyResult }) {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [expanded, setExpanded] = useState(false);

  return (
    <li className={styles.result}>
      {/* HEADER */}
      <div className={styles.cardHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.resultIndex}>{result.id}.</span>
          <h2 className={styles.resultName}>{result.bedrijfsnaam}</h2>
          <span className={styles.resultSector}>{result.sector}</span>
        </div>
        <div className={styles.scoreWrapper}>
          <span className={styles.scoreBadge}>{result.score}/10</span>
        </div>
      </div>

      {/* PROJECT TYPE ROW */}
      <div className={styles.projectTypeRow}>
        <span className={styles.projectType}><Building /> Bedrijf voor samenwerking</span>
        {result.matchKwaliteit && (
          <span className={`${styles.matchBadge} ${matchClass(result.matchKwaliteit)}`}>
            {result.matchKwaliteit}
          </span>
        )}
      </div>

      {/* META */}
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

          {result.machinepark && result.machinepark.length > 0 && (
            <div className={styles.infoRow}>
              <strong>Machinepark:</strong>
              <div className={styles.machineChips}>
                {result.machinepark.map((m) => (
                  <span key={m} className={styles.machineChip}>{m}</span>
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
          {expanded && (
            <button
              className={styles.btnContact}
              onClick={() => alert(`Contact: ${result.contactgegevens}`)}
            >
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

export default function CompanyResultPage() {
  const [searchParams] = useSearchParams();
  const [results, setResults] = useState<CompanyResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiPowered, setAiPowered] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState<string>('');

  const paramsString = searchParams.toString();

  useEffect(() => {
    const query = searchParams.get('query') || '';
    const locatie = searchParams.get('locatie') || '';
    const sector = searchParams.get('sector') || '';
    const regio = searchParams.get('regio') || '';
    setSearchedQuery(query);

    if (!query) {
      setResults([]);
      setLoading(false);
      setError('Voer een productomschrijving in om te zoeken.');
      return;
    }

    const fetchResults = async () => {
      try {
        const body: Record<string, unknown> = { query };
        const filters: Record<string, string> = {};
        if (locatie) filters.locatie = locatie;
        if (sector) filters.sector = sector;
        if (regio) filters.regio = regio;
        if (Object.keys(filters).length > 0) body.filters = filters;

        const response = await fetch(`${API_BASE_URL}/companies/prospect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error('Failed to fetch results');
        const data = await response.json();
        setAiPowered(data.ai_powered || false);

        // Map AI-scored results to CompanyResult format
        const mapped: CompanyResult[] = (data.results || []).map(
          (r: Record<string, unknown>, index: number) => ({
            id: (r.id as number) || index + 1,
            bedrijfsnaam: (r.bedrijfsnaam as string) || 'Onbekend bedrijf',
            sector: (r.sector as string) || 'Niet opgegeven',
            locatie: (r.locatie as string) || 'Niet opgegeven',
            beschrijving: (r.beschrijving as string) || '',
            waarom: (r.waarom as string) || '',
            score: (r.score as number) || 0,
            contactgegevens: (r.contactgegevens as string) || 'Niet beschikbaar',
            techstack: (r.techstack as string[]) || [],
            matchKwaliteit:
              (r.score as number) >= 8
                ? 'Sterke match'
                : (r.score as number) >= 5
                  ? 'Goede match'
                  : 'Gedeeltelijke match',
          }),
        );

        setResults(mapped.length > 0 ? mapped : []);
        if (mapped.length === 0) setError('Geen bedrijven gevonden voor deze zoekopdracht.');
      } catch (err) {
        console.error('Fout bij ophalen resultaten:', err);
        setError('Fout bij het ophalen van resultaten. Controleer of de backend draait.');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsString]);

  if (loading) return <p style={{ textAlign: 'center', padding: '60px' }}>AI analyseert bedrijven…</p>;

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>
        Bedrijfsresultaten{searchedQuery ? ` voor "${searchedQuery}"` : ''}
        {aiPowered && <span style={{ fontSize: '0.6em', marginLeft: '12px', color: '#22c55e' }}>AI-gescoord</span>}
      </h1>

      {/* ACTION BAR */}
      <div className={styles.actionBar}>
        <button className={styles.btnSave} onClick={() => {
          const q = searchParams.get('query') || '';
          const f: Record<string, string> = {};
          const loc = searchParams.get('locatie');
          const sec = searchParams.get('sector');
          const reg = searchParams.get('regio');
          if (loc) f.locatie = loc;
          if (sec) f.sector = sec;
          if (reg) f.regio = reg;
          saveToDatabase(q, f, results);
        }}>
          Opslaan
        </button>
        <button
          className={styles.btnExport}
          onClick={() => downloadAsExcel(results, 'bedrijf-resultaten.xlsx')}
        >
          Exporteren
        </button>
        <Link to="/keuze">
          <button className={styles.btnNew}>Nieuwe zoekopdracht</button>
        </Link>
      </div>

      {/* COUNT */}
      {error && <p style={{ color: '#ef4444', padding: '8px 0' }}>{error}</p>}
      <p className={styles.resultCount}>
        {results.length} bedrijf{results.length !== 1 ? 'en' : ''} gevonden
      </p>

      {/* LIST */}
      <ul className={styles.resultsList}>
        {results.map((result) => (
          <CompanyCard key={`${result.id}-${result.bedrijfsnaam}`} result={result} />
        ))}
      </ul>
    </main>
  );
}

// ── Save helper ───────────────────────────────────────────────────────────────

const saveToDatabase = async (query: string, filters: Record<string, string>, data: CompanyResult[]) => {
  try {
    const response = await fetch(`${API_BASE_URL}/searches/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        type: 'company',
        title: `Bedrijven: ${query}`,
        filters: Object.keys(filters).length > 0 ? filters : null,
        results: data,
      }),
    });
    if (!response.ok) throw new Error('Opslaan mislukt');
    alert('Zoekopdracht succesvol opgeslagen!');
  } catch (error) {
    console.error('Fout bij opslaan:', error);
    alert('Er is een fout opgetreden bij het opslaan.');
  }
};
