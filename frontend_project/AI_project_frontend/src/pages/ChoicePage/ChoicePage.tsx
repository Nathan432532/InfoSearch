import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './ChoicePage.module.css';
import { Briefcase, Building, Folder } from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────

type OptionType = 'job' | 'company';

interface Option {
  type: OptionType;
  icon: React.ReactNode;
  label: string;
  description: string;
  route: string;
}

// ── Data ──────────────────────────────────────────────────────────────────────

const OPTIONS: Option[] = [
  {
    type: 'job',
    icon: <Briefcase></Briefcase>,
    label: 'Job Applicatie',
    description: 'Zoek naar vacatures en solliciteer op interessante functies',
    route: '/search/job',
  },
  {
    type: 'company',
    icon: <Building></Building>,
    label: 'Bedrijf voor Project',
    description: 'Vind bedrijven voor samenwerking of projectopdrachten',
    route: '/search/company',
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function ChoicePage() {
  const [selected, setSelected] = useState<OptionType | null>(null);
  const navigate = useNavigate();

  const handleSubmit = () => {
    if (!selected) return;
    const option = OPTIONS.find((o) => o.type === selected);
    if (option) navigate(option.route);
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.card}>
          <h1 className={styles.title}>Wat zoek je?</h1>
          <p className={styles.subtitle}>Selecteer een optie om verder te gaan</p>

          <div className={styles.options}>
            {OPTIONS.map((option) => (
              <button
                key={option.type}
                type="button"
                className={`${styles.optionBtn} ${selected === option.type ? styles.selected : ''}`}
                onClick={() => setSelected(option.type)}
              >
                <div className={styles.icon}>{option.icon}</div>
                <div className={styles.optionContent}>
                  <span className={styles.optionLabel}>{option.label}</span>
                  <span className={styles.optionDescription}>{option.description}</span>
                </div>
              </button>
            ))}
          </div>

          <button
            className={styles.submitBtn}
            disabled={!selected}
            onClick={handleSubmit}
          >
            Doorgaan
          </button>

          <Link to="/saved" className={styles.savedLink}>
            <Folder size={16} /> Opgeslagen zoekopdrachten bekijken
          </Link>
        </div>
      </main>
    </div>
  );
}
