import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './SearchPage.module.css';
import { FolderOpen, File, Search } from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────────────

interface Filters {
    locatie: string;
    contract: string;
    sector: string;
    ervaringsniveau: string;
}

interface SearchPageProps {
    onSearch?: (query: string, files: File[], filters: Filters) => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function SearchPageJob({
    onSearch,
}: SearchPageProps) {
    const navigate = useNavigate();
    const [query, setQuery] = useState<string>('');
    const [files, setFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState<boolean>(false);
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [filters, setFilters] = useState<Filters>({
        locatie: '',
        contract: '',
        sector: '',
        ervaringsniveau: '',
    });

    const fileInputRef = useRef<HTMLInputElement>(null);

    // ── File handling ──────────────────────────────────────────────────────────
    const addFiles = useCallback((newFiles: FileList | null) => {
    if (!newFiles) return;
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      const toAdd = Array.from(newFiles).filter((f) => !existing.has(f.name));
      return [...prev, ...toAdd];
    });
  }, []);

  const removeFile = (fileName: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== fileName));
  };

  // ── Drag & drop handlers ───────────────────────────────────────────────────

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  // ── Form handlers ──────────────────────────────────────────────────────────

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    onSearch?.(trimmedQuery, files, filters);

    const params = new URLSearchParams({ query: trimmedQuery });
    if (filters.locatie) params.set('locatie', filters.locatie);
    if (filters.contract) params.set('contract_type', filters.contract);
    if (filters.sector) params.set('sector', filters.sector);
    if (filters.ervaringsniveau) params.set('ervaring', filters.ervaringsniveau);

    navigate(`/results/job?${params.toString()}`);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className={styles.page}>


      {/* MAIN */}
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

            {/* UPLOAD */}
            <div>
              <label className={styles.label}>Upload:</label>
              <div
                className={`${styles.uploadZone} ${isDragging ? styles.dragging : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className={styles.uploadZoneIcon}> <FolderOpen color="#000"></FolderOpen></div>
                <p className={styles.uploadZoneText}>
                  Sleep bestanden hierheen of klik om te bladeren.
                </p>
                <p className={styles.uploadZoneSubText}>Ondersteund: PDF, DOCX</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx"
                  style={{ display: 'none' }}
                  onChange={(e) => addFiles(e.target.files)}
                />
              </div>

              {files.length > 0 && (
                <div className={styles.fileList}>
                  {files.map((file) => (
                    <div key={file.name} className={styles.fileChip}>
                      <File />
                      {file.name}
                      <button
                        type="button"
                        className={styles.removeFileBtn}
                        onClick={() => removeFile(file.name)}
                        title="Verwijder"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
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
                    <label className={styles.filterLabel}>Contracttype</label>
                    <select
                      className={styles.filterSelect}
                      value={filters.contract}
                      onChange={(e) => handleFilterChange('contract', e.target.value)}
                    >
                      <option value="">Alle</option>
                      <option value="voltijds">Voltijds</option>
                      <option value="deeltijds">Deeltijds</option>
                      <option value="freelance">Freelance</option>
                      <option value="interim">Interim</option>
                    </select>
                  </div>

                  <div className={styles.filterGroup}>
                    <label className={styles.filterLabel}>Sector</label>
                    <input
                      type="text"
                      placeholder="bv. IT, Zorg..."
                      className={styles.filterInput}
                      value={filters.sector}
                      onChange={(e) => handleFilterChange('sector', e.target.value)}
                    />
                  </div>

                  <div className={styles.filterGroup}>
                    <label className={styles.filterLabel}>Ervaringsniveau</label>
                    <select
                      className={styles.filterSelect}
                      value={filters.ervaringsniveau}
                      onChange={(e) =>
                        handleFilterChange('ervaringsniveau', e.target.value)
                      }
                    >
                      <option value="">Alle</option>
                      <option value="junior">Junior</option>
                      <option value="medior">Medior</option>
                      <option value="senior">Senior</option>
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
