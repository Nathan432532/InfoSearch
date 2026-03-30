import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <main style={{ padding: "100px 20px", textAlign: "center", minHeight: "calc(100vh - 68px)", background: "linear-gradient(170deg, #f0faf5 0%, #e2f5ec 40%, #d4f0e4 100%)" }}>
      <h1 style={{ fontSize: "5rem", fontWeight: 800, background: "linear-gradient(135deg, rgb(16,191,124), rgb(13,153,99))", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", margin: 0 }}>404</h1>
      <h2 style={{ color: "#222", fontWeight: 700 }}>Pagina niet gevonden</h2>
      <p style={{ color: "#666" }}>Het lijkt erop dat de pagina die je zoekt niet (meer) bestaat.</p>
      
      <Link to="/home" style={{ 
        display: "inline-block", 
        marginTop: "20px", 
        padding: "12px 24px", 
        background: "linear-gradient(135deg, rgb(16,191,124), rgb(13,153,99))",
        color: "white", 
        textDecoration: "none",
        borderRadius: "12px",
        fontWeight: 600,
        boxShadow: "0 4px 16px rgba(16,191,124,0.3)"
      }}>
        Terug naar Home
      </Link>
    </main>
  );
};

export default NotFound;