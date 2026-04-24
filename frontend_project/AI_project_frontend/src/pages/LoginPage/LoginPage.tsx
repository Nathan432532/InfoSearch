import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import gsap from 'gsap';
import styles from './LoginPage.module.css';
import { Lock, User, Eye, EyeOff } from 'lucide-react';
import logoImg from '../../assets/infofarm.png';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const cardRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const tl = gsap.timeline();
    tl.fromTo(cardRef.current, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' });
    tl.fromTo(titleRef.current, { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, '-=0.3');
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (await login(username, password)) {
      navigate('/home');
    } else {
      setError('Ongeldige gebruikersnaam of wachtwoord');
      gsap.fromTo(cardRef.current, { x: -8 }, { x: 0, duration: 0.4, ease: 'elastic.out(1, 0.3)' });
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.backdrop} />
      <div className={styles.card} ref={cardRef}>
        <div className={styles.logoArea}>
          <div className={styles.logoCircle}>
            <img src={logoImg} alt="Infofarm" className={styles.logoImage} />
          </div>
          <h1 className={styles.title} ref={titleRef}>InfoSearch</h1>
          <p className={styles.subtitle}>Log in om verder te gaan</p>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <User size={18} className={styles.inputIcon} />
            <input
              className={styles.input}
              type="text"
              placeholder="Gebruikersnaam"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className={styles.inputGroup}>
            <Lock size={18} className={styles.inputIcon} />
            <input
              className={styles.input}
              type={showPassword ? 'text' : 'password'}
              placeholder="Wachtwoord"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
            <button
              type="button"
              className={styles.eyeBtn}
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button className={styles.submitBtn} type="submit">
            Inloggen
          </button>
        </form>
      </div>
    </div>
  );
}
