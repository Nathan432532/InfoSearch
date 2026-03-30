import { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import styles from './HomePage.module.css';
import { Briefcase, Building, Folder, Sparkles, ArrowRight } from 'lucide-react';

interface QuickAction {
  icon: React.ReactNode;
  label: string;
  description: string;
  route: string;
  accent: string;
}

const ACTIONS: QuickAction[] = [
  {
    icon: <Briefcase size={26} />,
    label: 'Vacatures zoeken',
    description: 'Vind relevante vacatures op basis van je criteria',
    route: '/search/job',
    accent: 'var(--accent)',
  },
  {
    icon: <Building size={26} />,
    label: 'Bedrijven prospecteren',
    description: 'AI-gestuurde bedrijfsmatching voor je product',
    route: '/search/company',
    accent: 'var(--accent)',
  },
  {
    icon: <Folder size={26} />,
    label: 'Opgeslagen resultaten',
    description: 'Bekijk je eerder opgeslagen zoekopdrachten',
    route: '/saved',
    accent: 'var(--accent)',
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const heroRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.fromTo(heroRef.current, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5 });
    tl.fromTo(
      cardsRef.current?.children ? Array.from(cardsRef.current.children) : [],
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.4, stagger: 0.1 },
      '-=0.2'
    );
  }, []);

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        {/* Hero */}
        <div className={styles.hero} ref={heroRef}>
          <div className={styles.heroBadge}>
            <Sparkles size={14} />
            <span>AI-gestuurd platform</span>
          </div>
          <h1 className={styles.heroTitle}>
            Welkom bij <span className={styles.brandAccent}>InfoSearch</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Vind de perfecte match tussen vacatures, bedrijven en jouw product — aangedreven door kunstmatige intelligentie.
          </p>
        </div>

        {/* Quick actions grid */}
        <div className={styles.grid} ref={cardsRef}>
          {ACTIONS.map((action) => (
            <button
              key={action.route}
              className={styles.actionCard}
              onClick={() => navigate(action.route)}
            >
              <div className={styles.actionIcon}>{action.icon}</div>
              <div className={styles.actionText}>
                <span className={styles.actionLabel}>{action.label}</span>
                <span className={styles.actionDesc}>{action.description}</span>
              </div>
              <ArrowRight size={18} className={styles.actionArrow} />
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}
