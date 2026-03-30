import styles from './Header.module.css';
import { Link, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Home, Folder, LogOut, User, ChevronDown } from 'lucide-react';
import logoImg from '../../assets/infofarm.png';

export default function Header() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { userName, logout } = useAuth();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
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

  return (
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
          <span className={styles.userName}>{userName || 'Admin'}</span>
          <ChevronDown size={14} className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`} />
        </button>
        {open && (
          <div className={styles.dropdown}>
            <button onClick={handleLogout} className={styles.dropdownItem}>
              <LogOut size={15} />
              <span>Uitloggen</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}