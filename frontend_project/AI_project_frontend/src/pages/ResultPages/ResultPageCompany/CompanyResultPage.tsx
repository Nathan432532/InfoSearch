import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { FaThumbsDown, FaThumbsUp } from 'react-icons/fa';
import gsap from 'gsap';
import styles from './CompanyResultPage.module.css';
import { downloadAsExcel } from '../../../scripts/downloadxl';
import { Building, Pin, Mail, Globe, Phone } from 'lucide-react';
import { API_BASE_URL } from '../../../api/client';

export interface CompanyResult {
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
  machinepark?: string[];
  businessTrigger?: string;
  matchKwaliteit?: 'Sterke match' | 'Goede match' | 'Gedeeltelijke match';
  saved_result_id?: number;
  saved_search_id?: number;
}

function matchClass(kwaliteit?: string): string {
  if (!kwaliteit) return '';
  if (kwaliteit === 'Sterke match') return styles.matchStrong;
  if (kwaliteit === 'Goede match') return styles.matchGood;
  return styles.matchPartial;
}

async function readErrorMessage(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return data?.detail || data?.message || fallback;
  } catch {
    return fallback;
  }
}

async function saveWholeSearch(query: string, filters: Record<string, string>, results: CompanyResult[]) {
  const response = await fetch(`${API_BASE_URL}/searches/save`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      type: 'company',
      title: `Bedrijven: ${query}`,
      filters: Object.keys(filters).length > 0 ? filters : null,
      results,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, 'Opslaan mislukt'));
  }
}

async function saveSingleResult(query: string, filters: Record<string, string>, result: CompanyResult) {
  const response = await fetch(`${API_BASE_URL}/searches/save-item`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      type: 'company',
      title: `Bedrijf: ${result.bedrijfsnaam}`,
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

function CompanyCard({
  result,
  searchQuery,
  filters,
  onSaved,
}: {
  result: CompanyResult;
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
      alert('Bedrijf opgeslagen.');
    } catch (error) {
      console.error('Fout bij opslaan van bedrijf:', error);
      alert(error instanceof Error ? error.message : 'Opslaan mislukt.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <li className={styles.result}>
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

      <div className={styles.projectTypeRow}>
        <span className={styles.projectType}><Building /> Bedrijf voor samenwerking</span>
        {result.matchKwaliteit && (
          <span className={`${styles.matchBadge} ${matchClass(result.matchKwaliteit)}`}>
            {result.matchKwaliteit}
          </span>
        )}
      </div>

      <div className={styles.metaRow}>
        <div className={styles.metaItem}>
          <span className={styles.metaIcon}><Pin /></span>
          <span>{result.locatie}</span>
        </div>
      </div>

      <p className={styles.resultDescription}>
        {expanded ? result.beschrijving : result.beschrijving.slice(0, 130) + '…'}
      </p>

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

      <div className={styles.cardFooter}>
        <div className={styles.footerLeft}>
          <button className={styles.btnMore} onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Toon minder' : 'Lees meer'}
          </button>
          <button className={styles.btnSaveItem} onClick={handleSave} disabled={saving}>
            {saving ? 'Bezig...' : 'Bewaar dit bedrijf'}
          </button>
          {expanded && (
            <button
              className={styles.btnContact}
              onClick={handleContactClick}
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

export default function CompanyResultPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const listRef = useRef<HTMLUListElement>(null);
  const lastRequestKeyRef = useRef<string | null>(null);
  const savedState = (location.state || {}) as {
    isSavedView?: boolean;
    results?: Array<Record<string, unknown>>;
    savedTitle?: string;
    savedQuery?: string;
  };
  const isSavedView = Boolean(savedState?.isSavedView);
  const savedResults = savedState?.results;
  const savedTitle = savedState?.savedTitle || '';
  const savedQuery = savedState?.savedQuery || '';

  const [results, setResults] = useState<CompanyResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiPowered, setAiPowered] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState<string>('');
  const [savingWholeSearch, setSavingWholeSearch] = useState(false);

  const paramsString = searchParams.toString();
  const requestKey = useMemo(() => `${paramsString}::saved=${isSavedView ? 1 : 0}::count=${savedResults?.length || 0}::title=${savedTitle}::query=${savedQuery}`,
    [paramsString, isSavedView, savedResults, savedTitle, savedQuery]);

  useEffect(() => {
    if (!loading && listRef.current) {
      const cards = Array.from(listRef.current.children);
      gsap.fromTo(
        cards,
        { opacity: 0, y: 32 },
        { opacity: 1, y: 0, duration: 0.45, stagger: 0.08, ease: 'power3.out', clearProps: 'transform' }
      );
    }
  }, [loading, results.length]);

  useEffect(() => {
    if (lastRequestKeyRef.current === requestKey) return;
    lastRequestKeyRef.current = requestKey;

    if (isSavedView && savedResults) {
      const mapped: CompanyResult[] = savedResults.map((r, index) => ({
        id: Number(r.bedrijf_id || r.id) || index + 1,
        displayRank: index + 1,
        bedrijfsnaam: (r.bedrijfsnaam as string) || 'Onbekend bedrijf',
        sector: (r.sector as string) || 'Niet opgegeven',
        locatie: (r.locatie as string) || 'Niet opgegeven',
        beschrijving: (r.beschrijving as string) || '',
        waarom: (r.waarom as string) || '',
        score: (r.score as number) || 0,
        contactgegevens: (r.contactgegevens as string) || 'Niet beschikbaar',
        techstack: ((r.techstack || r.tech_stack || r.technologies) as string[]) || [],
        machinepark: ((r.machinepark || r.machine_park) as string[]) || undefined,
        businessTrigger: (r.businessTrigger || r.business_trigger) as string || undefined,
        saved_result_id: (r.saved_result_id as number) || undefined,
        saved_search_id: (r.saved_search_id as number) || undefined,
        matchKwaliteit:
          (r.score as number) >= 8 ? 'Sterke match'
            : (r.score as number) >= 5 ? 'Goede match'
              : 'Gedeeltelijke match',
      }));
      setResults(mapped);
      setSearchedQuery(savedTitle || savedQuery || '');
      setAiPowered(true);
      setLoading(false);
      return;
    }

    const query = searchParams.get('query') || '';
    const locatie = searchParams.get('locatie') || '';
    const sector = searchParams.get('sector') || '';
    const regio = searchParams.get('regio') || '';
    const bedrijfsgrootte = searchParams.get('bedrijfsgrootte') || '';
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
        if (bedrijfsgrootte) filters.bedrijfsgrootte = bedrijfsgrootte;
        if (regio) filters.regio = regio;
        if (Object.keys(filters).length > 0) body.filters = filters;

        const response = await fetch(`${API_BASE_URL}/companies/prospect`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error('Failed to fetch results');
        const data = await response.json();
        setAiPowered(data.ai_powered || false);

        const mapped: CompanyResult[] = (data.results || []).map((r: Record<string, unknown>, index: number) => ({
          id: Number(r.id) || index + 1,
          displayRank: index + 1,
          bedrijfsnaam: (r.bedrijfsnaam as string) || 'Onbekend bedrijf',
          sector: (r.sector as string) || 'Niet opgegeven',
          locatie: (r.locatie as string) || 'Niet opgegeven',
          beschrijving: (r.beschrijving as string) || '',
          waarom: (r.waarom as string) || '',
          score: (r.score as number) || 0,
          contactgegevens: (r.contactgegevens as string) || 'Niet beschikbaar',
          techstack: ((r.techstack || r.tech_stack || r.technologies) as string[]) || [],
          machinepark: ((r.machinepark || r.machine_park) as string[]) || undefined,
          businessTrigger: (r.businessTrigger || r.business_trigger) as string || undefined,
          matchKwaliteit:
            (r.score as number) >= 8 ? 'Sterke match'
              : (r.score as number) >= 5 ? 'Goede match'
                : 'Gedeeltelijke match',
        }));

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
  }, [requestKey, isSavedView, savedResults, savedTitle, savedQuery, searchParams]);

  const activeFilters = useMemo(() => {
    const filters: Record<string, string> = {};
    const loc = searchParams.get('locatie');
    const sec = searchParams.get('sector');
    const size = searchParams.get('bedrijfsgrootte');
    const reg = searchParams.get('regio');
    if (loc) filters.locatie = loc;
    if (sec) filters.sector = sec;
    if (size) filters.bedrijfsgrootte = size;
    if (reg) filters.regio = reg;
    return filters;
  }, [searchParams]);

  const handleSaveWholeSearch = async () => {
    try {
      setSavingWholeSearch(true);
      const query = searchParams.get('query') || searchedQuery;
      await saveWholeSearch(query, activeFilters, results);
      alert('Zoekopdracht succesvol opgeslagen.');
    } catch (error) {
      console.error('Fout bij opslaan van zoekopdracht:', error);
      alert(error instanceof Error ? error.message : 'Er is een fout opgetreden bij het opslaan.');
    } finally {
      setSavingWholeSearch(false);
    }
  };

  if (loading) return <p style={{ textAlign: 'center', padding: '60px' }}>AI analyseert bedrijven…</p>;

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>
        Bedrijfsresultaten{searchedQuery ? ` voor "${searchedQuery}"` : ''}
        {aiPowered && <span style={{ fontSize: '0.6em', marginLeft: '12px', color: '#22c55e' }}>AI-gescoord</span>}
      </h1>

      <div className={styles.actionBar}>
        <button className={styles.btnSave} onClick={handleSaveWholeSearch} disabled={savingWholeSearch || results.length === 0}>
          {savingWholeSearch ? 'Bezig...' : 'Hele zoekopdracht opslaan'}
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

      {error && <p style={{ color: '#ef4444', padding: '8px 0' }}>{error}</p>}
      <p className={styles.resultCount}>
        {results.length} bedrijf{results.length !== 1 ? 'en' : ''} gevonden
      </p>

      <ul className={styles.resultsList} ref={listRef}>
        {results.map((result) => (
          <CompanyCard
            key={`${result.id}-${result.bedrijfsnaam}`}
            result={result}
            searchQuery={searchParams.get('query') || searchedQuery}
            filters={activeFilters}
            onSaved={() => undefined}
          />
        ))}
      </ul>
    </main>
  );
}
