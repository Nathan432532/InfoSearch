import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './SearchPage.module.css';
import { Search } from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────────────

interface Filters {
    locatie: string;
    sector: string;
    bedrijfsgrootte: string;
    regio: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SearchPageCompany() {
    const navigate = useNavigate();
    const [query, setQuery] = useState<string>('');
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [filters, setFilters] = useState<Filters>({
        locatie: '',
        sector: '',
        bedrijfsgrootte: '',
        regio: '',
    });

    // ── Form handlers ──────────────────────────────────────────────────────────

    const handleFilterChange = (key: keyof Filters, value: string) => {
        setFilters((prev) => ({ ...prev, [key]: value }));
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!query.trim()) return;

        const params = new URLSearchParams({ query: query.trim() });
        if (filters.locatie) params.set('locatie', filters.locatie);
        if (filters.sector) params.set('sector', filters.sector);
        if (filters.regio) params.set('regio', filters.regio);

        navigate(`/results/company?${params.toString()}`);
    };

    // ── Render ─────────────────────────────────────────────────────────────────

    return (
        <div className={styles.page}>
            <main className={styles.main}>
                <div className={styles.dashboard}>
                    <h1 className={styles.dashboardTitle}>Nieuwe zoekopdracht</h1>

                    <form className={styles.form} onSubmit={handleSubmit}>

                        {/* QUERY */}
                        <div>
                            <label className={styles.label}>Query:</label>
                            <input
                                type="text"
                                required
                                placeholder="Voer hier je query in."
                                className={styles.queryInput}
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                            />
                        </div>

                        {/* FILTERS */}
                        <div>
                            <div className={styles.filtersRow}>
                                <label className={styles.label} style={{ marginBottom: 0 }}>
                                    Filters
                                </label>
                                <button
                                    type="button"
                                    className={`${styles.filterToggleBtn} ${showFilters ? styles.active : ''}`}
                                    onClick={() => setShowFilters((v) => !v)}
                                    title="Filters tonen/verbergen"
                                >
                                    {showFilters ? '✕' : '☰'}
                                </button>
                            </div>

                            {showFilters && (
                                <div className={styles.filterPanel}>
                                    <div className={styles.filterGroup}>
                                        <label className={styles.filterLabel}>Locatie</label>
                                        <input
                                            type="text"
                                            placeholder="bv. Gent, Brussel..."
                                            className={styles.filterInput}
                                            value={filters.locatie}
                                            onChange={(e) => handleFilterChange('locatie', e.target.value)}
                                        />
                                    </div>

                                    <div className={styles.filterGroup}>
                                        <label className={styles.filterLabel}>Sector</label>
                                        <input
                                            type="text"
                                            placeholder="bv. IT, Industrie..."
                                            className={styles.filterInput}
                                            value={filters.sector}
                                            onChange={(e) => handleFilterChange('sector', e.target.value)}
                                        />
                                    </div>

                                    <div className={styles.filterGroup}>
                                        <label className={styles.filterLabel}>Bedrijfsgrootte</label>
                                        <select
                                            className={styles.filterSelect}
                                            value={filters.bedrijfsgrootte}
                                            onChange={(e) => handleFilterChange('bedrijfsgrootte', e.target.value)}
                                        >
                                            <option value="">Alle</option>
                                            <option value="klein">Klein (&lt;50)</option>
                                            <option value="middel">Middel (50–250)</option>
                                            <option value="groot">Groot (&gt;250)</option>
                                        </select>
                                    </div>

                                    <div className={styles.filterGroup}>
                                        <label className={styles.filterLabel}>Regio</label>
                                        <select
                                            className={styles.filterSelect}
                                            value={filters.regio}
                                            onChange={(e) => handleFilterChange('regio', e.target.value)}
                                        >
                                            <option value="">Alle</option>
                                            <option value="vlaanderen">Vlaanderen</option>
                                            <option value="wallonie">Wallonië</option>
                                            <option value="brussel">Brussel</option>
                                        </select>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* SUBMIT */}
                        <button type="submit" className={styles.submitBtn}>
                            <Search /> Start zoekopdracht
                        </button>

                    </form>
                </div>
            </main>
        </div>
    );
}
