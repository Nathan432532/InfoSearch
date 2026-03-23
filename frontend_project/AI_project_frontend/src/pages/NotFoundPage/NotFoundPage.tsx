import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <main style={{ padding: "100px 20px", textAlign: "center" }}>
      <h1 style={{ fontSize: "3rem", color: "#333" }}>404</h1>
      <h2>Oeps! Pagina niet gevonden</h2>
      <p>Het lijkt erop dat de pagina die je zoekt niet (meer) bestaat.</p>
      
      <Link to="/search" style={{ 
        display: "inline-block", 
        marginTop: "20px", 
        padding: "10px 20px", 
        backgroundColor: "#007bff", 
        color: "white", 
        textDecoration: "none",
        borderRadius: "5px" 
      }}>
        Terug naar Zoeken
      </Link>
    </main>
  );
};

export default NotFound;