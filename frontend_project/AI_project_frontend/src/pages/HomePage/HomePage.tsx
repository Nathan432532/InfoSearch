import { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import styles from './HomePage.module.css';
import { Building, Briefcase, ArrowRight, Clock, Sparkles, ChevronRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { runVdabSync } from '../../api/jobs';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

interface RecentSearch {
  id: number;
  titel: string;
  title?: string;
  query: string;
  datum: string;
  type: 'job' | 'company';
  results?: Record<string, unknown>[];
}

export default function HomePage() {
  const navigate = useNavigate();
  const { userName, isAdmin } = useAuth();
  const heroRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const historyRef = useRef<HTMLElement>(null);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.fromTo(heroRef.current, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.5 });
    tl.fromTo(
      ctaRef.current?.children ? Array.from(ctaRef.current.children) : [],
      { opacity: 0, y: 36, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 0.5, stagger: 0.13 },
      '-=0.3'
    );
    tl.fromTo(historyRef.current, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.4 }, '-=0.15');
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/searches/saved`, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Ophalen opgeslagen zoekopdrachten mislukt');
        return r.json();
      })
      .then((data: { searches?: { company?: RecentSearch[]; job?: RecentSearch[] } }) => {
        const combined = [
          ...(data.searches?.company || []),
          ...(data.searches?.job || []),
        ]
          .sort((a, b) => new Date(b.datum).getTime() - new Date(a.datum).getTime())
          .slice(0, 5)
          .map((r) => ({ ...r, titel: r.titel || r.title || r.query }));

        setRecentSearches(combined);
      })
      .catch(() => setRecentSearches([]));
  }, []);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Goedemorgen';
    if (h < 18) return 'Goedemiddag';
    return 'Goedenavond';
  };

  const shownName = sessionStorage.getItem('infosearch_display') || userName || 'Admin';

  const handleManualVdabSync = async () => {
    try {
      setIsSyncing(true);
      setSyncMessage('VDAB sync loopt...');
      const result = await runVdabSync(100);
      const upserted = result?.import?.upserted ?? 0;
      const fetched = result?.import?.fetched ?? 0;
      setSyncMessage(`VDAB sync klaar. ${upserted} vacatures verwerkt, ${fetched} opgehaald.`);
    } catch (error) {
      console.error(error);
      setSyncMessage('VDAB sync mislukt. Check backend logs.');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        {/* Hero */}
        <div className={styles.hero} ref={heroRef}>
          <div className={styles.heroBadge}>
            <Sparkles size={13} />
            <span>AI-gestuurd platform</span>
          </div>
          <h1 className={styles.heroTitle}>
            {greeting()}, <span className={styles.brandAccent}>{shownName}</span>
          </h1>
          <p className={styles.heroSubtitle}>Wat wil je vandaag ontdekken?</p>
        </div>

        {/* Two primary CTA cards */}
        <div className={styles.ctaGrid} ref={ctaRef}>
          <button
            className={`${styles.ctaCard} ${styles.ctaCardSecondary}`}
            onClick={() => navigate('/search/job')}
          >
            <div className={styles.ctaShine} />
            <div className={styles.ctaCardContent}>
              <div className={styles.ctaIcon}><Briefcase size={30} /></div>
              <div className={styles.ctaText}>
                <span className={styles.ctaLabel}>Vacatures zoeken</span>
                <span className={styles.ctaDesc}>
                  Doorzoek actuele vacatures op basis van profiel en criteria
                </span>
              </div>
              <ArrowRight size={22} className={styles.ctaArrow} />
            </div>
          </button>

          <button
            className={`${styles.ctaCard} ${styles.ctaCardSecondary}`}
            onClick={() => navigate('/search/company')}
          >
            <div className={styles.ctaShine} />
            <div className={styles.ctaCardContent}>
              <div className={styles.ctaIcon}><Building size={30} /></div>
              <div className={styles.ctaText}>
                <span className={styles.ctaLabel}>Bedrijven prospecteren</span>
                <span className={styles.ctaDesc}>
                  AI-gestuurde bedrijfsmatching voor jouw product of dienst
                </span>
              </div>
              <ArrowRight size={22} className={styles.ctaArrow} />
            </div>
          </button>

          {isAdmin && (
            <button
              className={`${styles.ctaCard} ${styles.ctaCardSecondary} ${styles.ctaCardFullWidth}`}
              onClick={handleManualVdabSync}
              disabled={isSyncing}
            >
              <div className={styles.ctaShine} />
              <div className={styles.ctaCardContent}>
                <div className={styles.ctaIcon}><Sparkles size={30} /></div>
                <div className={styles.ctaText}>
                  <span className={styles.ctaLabel}>VDAB handmatig verversen</span>
                  <span className={styles.ctaDesc}>
                    Trek nu handmatig de VDAB data binnen
                  </span>
                </div>
                <ArrowRight size={22} className={styles.ctaArrow} />
              </div>
            </button>
          )}
        </div>

        {syncMessage ? <p className={styles.emptyHistory}>{syncMessage}</p> : null}

        {/* Recent history */}
        <section className={styles.historySection} ref={historyRef}>
          <div className={styles.historySectionHeader}>
            <div className={styles.historyHeading}>
              <Clock size={15} />
              <span>Recente zoekopdrachten</span>
            </div>
            <button className={styles.viewAllBtn} onClick={() => navigate('/saved')}>
              Alles bekijken <ChevronRight size={14} />
            </button>
          </div>

          {recentSearches.length === 0 ? (
            <p className={styles.emptyHistory}>Nog geen zoekopdrachten opgeslagen.</p>
          ) : (
            <div className={styles.historyList}>
              {recentSearches.map((item) => (
                <button
                  key={item.id}
                  className={styles.historyItem}
                  onClick={() =>
                    navigate(`/results/${item.type}`, {
                      state: {
                        isSavedView: true,
                        results: item.results || [],
                        savedTitle: item.titel,
                        savedQuery: item.query,
                      },
                    })
                  }
                >
                  <span
                    className={`${styles.historyTypeDot} ${
                      item.type === 'company' ? styles.dotCompany : styles.dotJob
                    }`}
                  />
                  <span className={styles.historyTitle}>{item.titel}</span>
                  <span className={styles.historyQuery}>"{item.query}"</span>
                  <ChevronRight size={14} className={styles.historyArrow} />
                </button>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
