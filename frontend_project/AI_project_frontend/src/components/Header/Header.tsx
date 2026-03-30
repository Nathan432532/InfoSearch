import styles from './Header.module.css';
import { Link } from 'react-router-dom';
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface HeaderProps {
    userName?: string;
}
export default function Header({
    userName = 'Voornaam Achternaam'}: HeaderProps) {
        const [open, setopen] = useState(false)
        const navigate = useNavigate()

        const handleLogout = () => {
            // Hier kun je de logica voor het uitloggen implementeren, zoals het verwijderen van tokens of het resetten van de gebruikersstatus.
            // Na het uitloggen kun je de gebruiker terug naar de loginpagina navigeren.
            console.log('User logged out');
            navigate('/login');
        }
        return (
        

<div className={styles.page}>

      {/* HEADER */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <Link to="/" className={styles.logoTitle}>
          <img src="/src/assets/infofarm.png" alt="InfoSearch Logo" className={styles.logoIcon} />
          </Link>
          <Link to="/" className={styles.logoTitle}>
            <h1 className={styles.logoTitle}>InfoSearch</h1>
          </Link>
        </div>
        <nav className={styles.nav}>
          <Link to="/saved" className={styles.navLink}>Opgeslagen</Link>
        </nav>
        <div className={styles.profile}>
          <span className={styles.userName}>{userName}</span>
          <div className={styles.profileIcon}
            onClick={() => setopen(!open)}
          >👤</div>
            {open && (
                <div className={styles.dropdown}>
                    <button onClick={handleLogout} className={styles.dropdownItem}>Logout</button>
                </div>
            )}
        </div>
      </header>
</div>)}