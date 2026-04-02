import styles from './Header.module.css';
import { Link, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Home, Folder, LogOut, User, ChevronDown, Settings, X } from 'lucide-react';
import logoImg from '../../assets/infofarm.png';

export default function Header() {
  const [open, setOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { userName, logout } = useAuth();
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDisplayName(sessionStorage.getItem('infosearch_display') || userName || 'Admin');
  }, [userName]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSaveSettings = () => {
    const trimmed = displayName.trim() || 'Admin';
    sessionStorage.setItem('infosearch_display', trimmed);
    setSettingsOpen(false);
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const isActive = (path: string) => location.pathname === path;
  const shownName = sessionStorage.getItem('infosearch_display') || userName || 'Admin';

  return (
    <>
      <header className={styles.header}>
        <Link to="/home" className={styles.logoLink}>
          <img src={logoImg} alt="Infofarm" className={styles.logoImg} />
          <span className={styles.logoText}>InfoSearch</span>
        </Link>

        <nav className={styles.nav}>
          <Link to="/home" className={`${styles.navLink} ${isActive('/home') ? styles.navLinkActive : ''}`}>
            <Home size={16} />
            <span>Home</span>
          </Link>
          <Link to="/saved" className={`${styles.navLink} ${isActive('/saved') ? styles.navLinkActive : ''}`}>
            <Folder size={16} />
            <span>Opgeslagen</span>
          </Link>
        </nav>

        <div className={styles.profile} ref={dropdownRef}>
          <button className={styles.profileBtn} onClick={() => setOpen(!open)}>
            <div className={styles.avatar}>
              <User size={16} />
            </div>
            <span className={styles.userName}>{shownName}</span>
            <ChevronDown size={14} className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`} />
          </button>
          {open && (
            <div className={styles.dropdown}>
              <button onClick={() => { setOpen(false); setSettingsOpen(true); }} className={styles.dropdownItem}>
                <Settings size={15} />
                <span>Instellingen</span>
              </button>
              <div className={styles.dropdownDivider} />
              <button onClick={handleLogout} className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}>
                <LogOut size={15} />
                <span>Uitloggen</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Settings modal */}
      {settingsOpen && (
        <div className={styles.modalOverlay} onClick={() => setSettingsOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>Instellingen</h2>
              <button className={styles.modalClose} onClick={() => setSettingsOpen(false)}><X size={18} /></button>
            </div>
            <div className={styles.modalBody}>
              <label className={styles.settingsLabel}>Weergavenaam</label>
              <input
                className={styles.settingsInput}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Admin"
                autoFocus
              />
              <label className={styles.settingsLabel} style={{ marginTop: '16px' }}>Ingelogd als</label>
              <p className={styles.settingsValue}>{userName || 'admin'}</p>
              <label className={styles.settingsLabel}>API endpoint</label>
              <p className={styles.settingsValue}>{(import.meta.env.VITE_API_URL || 'http://localhost:8000')}</p>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.modalCancel} onClick={() => setSettingsOpen(false)}>Annuleren</button>
              <button className={styles.modalSave} onClick={handleSaveSettings}>Opslaan</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}