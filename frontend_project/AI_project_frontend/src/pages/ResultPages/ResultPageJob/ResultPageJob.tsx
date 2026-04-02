import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaThumbsUp, FaThumbsDown } from 'react-icons/fa';
import styles from './JobResultPage.module.css';
import { downloadAsExcel } from '../../../scripts/downloadxl';
import { Pin, CircuitBoard } from 'lucide-react';


const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
// ── Types ─────────────────────────────────────────────────────────────────────

export interface JobResult {
  id: number;
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

// ── Dummy data ────────────────────────────────────────────────────────────────

const DUMMY_RESULTS: JobResult[] = [
  {
    id: 1,
    bedrijfsnaam: 'METAL-FORMING BELGIUM',
    sector: 'Zware Metaalindustrie',
    locatie: 'Staalweg 88, 3600 Genk, Limburg',
    beschrijving:
      'Metal-Forming Belgium heeft een technische infrastructuur die perfect aansluit. Ze gebruiken Siemens S7-1500 systemen en Profinet, wat direct in lijn is met het gevraagde profiel.',
    waarom:
      'De tech-stack van Metal-Forming Belgium bevat exact dezelfde componenten als vereist. Dit zorgt voor een optimale match met jouw profiel.',
    score: 10,
    contactgegevens: 'Luc Mertens, Plant Manager — l.mertens@metalforming.be — +32 89 77 88 99',
    techstack: ['Siemens S7-1500', 'Sinamics Drives', 'Profinet', 'Safety PLC'],
    vacatureTitel: 'PLC & Drive Specialist',
    vacatureReferentie: 'VDAB-2024-4455',
    urgentie: 'Kritiek',
    keywords: ['PLC', 'drives', 'Siemens', 'industriële elektriciteit', 'storingstechnieker'],
    businessTrigger: 'Aanleg van een compleet nieuwe productielijn voor chassis-onderdelen van elektrische voertuigen.',
  },
  {
    id: 2,
    bedrijfsnaam: 'AGRO-BOTICS NV',
    sector: 'Landbouwmechanisatie & Robotica',
    locatie: 'Kouterstraat 15, 8500 Kortrijk, West-Vlaanderen',
    beschrijving:
      'AGRO-BOTICS NV heeft een sterke focus op robotica en autonome systemen. Ze gebruiken CAN-bus en Linux-based controllers, wat goed aansluit bij het technische profiel.',
    waarom:
      'De tech-stack en het machinepark passen goed aan voor het gevraagde profiel, zeker voor buitendienst en elektrotechnische taken.',
    score: 8,
    contactgegevens: 'Dirk Vanhecke, Technisch Directeur — d.vanhecke@agrobotics.be — +32 56 12 34 56',
    techstack: ['CODESYS', 'CAN-bus', 'Linux-based controllers', 'Python (scripting)'],
    vacatureTitel: 'Field Service Engineer - Autonome Maaiers',
    vacatureReferentie: 'VDAB-2024-9988',
    urgentie: 'Hoog',
    keywords: ['service engineer', 'robotica', 'CAN-bus', 'buitendienst', 'elektrotechniek'],
    businessTrigger: 'Lancering van een nieuwe generatie zelfrijdende oogstmachines en internationale expansie naar de Franse markt.',
  },
  {
    id: 3,
    bedrijfsnaam: 'BREW-TECH AUTOMATION',
    sector: 'Voedingsmiddelenindustrie (Brouwerijen)',
    locatie: 'Brouwerijstraat 1, 3080 Tervuren, Vlaams-Brabant',
    beschrijving:
      'Brew-Tech Automation is bezig met een modernisering van hun PLC-sturingen. Ze werken met Schneider Electric en SCADA-systemen in een productieomgeving.',
    waarom:
      'Hoewel er geen directe Siemens-ervaring vereist is, biedt de omgeving een interessante uitdaging voor iemand met brede PLC-kennis en interesse in de voedingssector.',
    score: 5,
    contactgegevens: 'Sarah Janssens, Maintenance Manager — maintenance@brewtech.com — +32 2 444 55 66',
    techstack: ['Schneider Electric (EcoStruxure)', 'Wonderware InTouch (SCADA)', 'Modbus TCP'],
    vacatureTitel: 'Automatisatie Technieker (Shift)',
    vacatureReferentie: 'VDAB-2024-3322',
    urgentie: 'Gemiddeld',
    keywords: ['onderhoud', 'storingen', 'Schneider', 'voeding', 'HMI'],
    businessTrigger: 'Modernisering van de bestaande PLC-sturingen van S5 naar de nieuwste standaarden en uitbreiding van de productiecapaciteit met 20%.',
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function urgencyClass(urgentie?: string): string {
  if (!urgentie) return '';
  const lower = urgentie.toLowerCase();
  if (lower === 'kritiek') return styles.urgencyCritical;
  if (lower === 'hoog') return styles.urgencyHigh;
  return styles.urgencyMedium;
}

// ── Sub-component: JobCard ────────────────────────────────────────────────────

function JobCard({ result }: { result: JobResult }) {
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
  const [results, setResults] = useState<JobResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/job-results`);
        if (!response.ok) throw new Error('Failed to fetch results');
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Onbekende fout');
        setResults(DUMMY_RESULTS);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  if (loading) return <p style={{ textAlign: 'center', padding: '60px' }}>Laden…</p>;
  if (results.length === 0) setResults(DUMMY_RESULTS);

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>Vacature Resultaten</h1>

      {/* ACTION BAR */}
      <div className={styles.actionBar}>
        <button className={styles.btnSave} onClick={() => saveToDatabase(results)}>
          Opslaan
        </button>
        <button className={styles.btnExport} onClick={() => downloadAsExcel(results, 'vacature-resultaten.xlsx')}>
          Exporteren
        </button>
        <Link to="/keuze">
          <button className={styles.btnNew}>Nieuwe zoekopdracht</button>
        </Link>
      </div>

      {/* COUNT */}
      <p className={styles.resultCount}>{results.length} vacature{results.length !== 1 ? 's' : ''} gevonden</p>

      {/* LIST */}
      <ul className={styles.resultsList}>
        {results.map((result) => (
          <JobCard key={`${result.id}-${result.bedrijfsnaam}`} result={result} />
        ))}
      </ul>
    </main>
  );
}

// ── Save helper ───────────────────────────────────────────────────────────────

const saveToDatabase = async (data: JobResult | JobResult[]) => {
  try {
    const response = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Opslaan mislukt');
    alert('Data succesvol opgeslagen!');
  } catch (error) {
    console.error('Fout bij opslaan:', error);
    alert('Er is een fout opgetreden bij het opslaan.');
  }
};
