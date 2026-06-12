import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { FaThumbsUp, FaThumbsDown } from 'react-icons/fa';
import styles from './JobResultPage.module.css';
import { downloadAsExcel } from '../../../scripts/downloadxl';
import { Pin, CircuitBoard, Mail, Globe, Phone } from 'lucide-react';
import { API_BASE_URL } from '../../../api/client';
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

interface ContactItem {
  type: 'email' | 'phone' | 'url' | 'text';
  value: string;
  label: string;
}

function parseContactgegevens(str: string): ContactItem[] {
  if (!str || str.toLowerCase() === 'niet beschikbaar' || str.trim() === '-') {
    return [];
  }

  const parts = str.split(/\s+-\s+/);
  const contactItems: ContactItem[] = [];

  const interimAgencies = [
    { name: 'VTC', pattern: /vtc\.be/i },
    { name: 'Accent', pattern: /accent\.be/i },
    { name: 'Randstad', pattern: /randstad\.be/i },
    { name: 'Adecco', pattern: /adecco\.be/i },
    { name: 'Start People', pattern: /startpeople\.be/i },
    { name: 'Manpower', pattern: /manpower\.be/i },
    { name: 'ASAP', pattern: /asap\.be/i },
    { name: 'Jobmatch', pattern: /jobmatch\.be/i },
    { name: 'Synergie', pattern: /synergiejobs\.be/i },
    { name: 'Actief', pattern: /actief\.be/i },
    { name: 'Ago', pattern: /ago\.jobs/i },
    { name: 'Select HR', pattern: /selecthr\.be/i },
    { name: 'Team Power', pattern: /teampower\.be/i },
    { name: 'Forum Jobs', pattern: /forumjobs\.be/i },
    { name: 'Tempo-Team', pattern: /tempo-team\.be/i },
    { name: 'Let\'s Work', pattern: /letswork\.be/i },
    { name: 'Unique', pattern: /unique\.be/i },
    { name: 'SD Worx', pattern: /sdworx\.be/i },
    { name: 'Liantis', pattern: /liantis\.be/i }
  ];

  const portalPatterns = [
    /oraclecloud\.com/i, /workday/i, /successfactors/i, /taleo\.net/i,
    /recruitee\.com/i, /cvwarehouse\.com/i, /jobtoolz\.be/i, /vacancy/i,
    /sollicitatie/i, /jobs\./i, /careers/i, /hcmUI/i
  ];

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    if (trimmed.includes('@') && !trimmed.includes(' ') && !trimmed.includes('/')) {
      let agencyName = '';
      for (const agency of interimAgencies) {
        if (agency.pattern.test(trimmed)) {
          agencyName = agency.name;
          break;
        }
      }
      const label = agencyName ? `${trimmed} (via recruiter: ${agencyName})` : trimmed;
      contactItems.push({ type: 'email', value: trimmed, label });
    }
    else if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('www.') || trimmed.includes('.com/') || trimmed.includes('.be/')) {
      let isPortal = false;
      for (const pat of portalPatterns) {
        if (pat.test(trimmed)) {
          isPortal = true;
          break;
        }
      }

      let label = 'Website';
      if (isPortal) {
        label = 'Online sollicitatieportaal';
      } else {
        try {
          let cleanUrl = trimmed;
          if (!cleanUrl.startsWith('http')) {
            cleanUrl = 'https://' + cleanUrl;
          }
          const urlObj = new URL(cleanUrl);
          label = urlObj.hostname.replace('www.', '');
        } catch {
          label = 'Website';
        }
      }
      contactItems.push({ type: 'url', value: trimmed.startsWith('www.') ? 'https://' + trimmed : trimmed, label });
    }
    else if (/^[+\d\s\/\.\-]+$/.test(trimmed) && trimmed.replace(/\D/g, '').length >= 6) {
      contactItems.push({ type: 'phone', value: trimmed, label: trimmed });
    }
    else {
      contactItems.push({ type: 'text', value: trimmed, label: trimmed });
    }
  }

  return contactItems;
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

  const handleContactClick = () => {
    const contactItems = parseContactgegevens(result.contactgegevens);
    if (contactItems.length === 0) {
      alert('Geen contactgegevens beschikbaar.');
      return;
    }
    const emailItem = contactItems.find(i => i.type === 'email');
    if (emailItem) {
      window.location.href = `mailto:${emailItem.value}`;
      return;
    }
    const urlItem = contactItems.find(i => i.type === 'url');
    if (urlItem) {
      window.open(urlItem.value, '_blank', 'noopener,noreferrer');
      return;
    }
    const phoneItem = contactItems.find(i => i.type === 'phone');
    if (phoneItem) {
      window.location.href = `tel:${phoneItem.value}`;
      return;
    }
    alert(`Contact: ${result.contactgegevens}`);
  };

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

          <div className={styles.infoRow} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <strong>Contactgegevens:</strong>
            {(() => {
              const contactItems = parseContactgegevens(result.contactgegevens);
              if (contactItems.length === 0) {
                return <span style={{ color: '#888', fontStyle: 'italic' }}>Niet beschikbaar</span>;
              }
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                  {contactItems.map((item, idx) => {
                    if (item.type === 'email') {
                      return (
                        <a
                          key={idx}
                          href={`mailto:${item.value}`}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'rgb(16, 191, 124)', textDecoration: 'none', fontWeight: 600 }}
                          title="Stuur een e-mail"
                        >
                          <Mail size={16} />
                          {item.label}
                        </a>
                      );
                    }
                    if (item.type === 'url') {
                      return (
                        <a
                          key={idx}
                          href={item.value}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'rgb(16, 191, 124)', textDecoration: 'none', fontWeight: 600 }}
                          title="Bezoek website"
                        >
                          <Globe size={16} />
                          {item.label}
                        </a>
                      );
                    }
                    if (item.type === 'phone') {
                      return (
                        <a
                          key={idx}
                          href={`tel:${item.value}`}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'rgb(16, 191, 124)', textDecoration: 'none', fontWeight: 600 }}
                          title="Bellen"
                        >
                          <Phone size={16} />
                          {item.label}
                        </a>
                      );
                    }
                    return (
                      <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#555' }}>
                        {item.label}
                      </span>
                    );
                  })}
                </div>
              );
            })()}
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
            <button className={styles.btnContact} onClick={handleContactClick}>
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
        if (sector) filters.sector = sector;
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
    const sector = searchParams.get('sector');
    const ervaring = searchParams.get('ervaring');
    if (locatie) filters.locatie = locatie;
    if (contractType) filters.contract_type = contractType;
    if (sector) filters.sector = sector;
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
