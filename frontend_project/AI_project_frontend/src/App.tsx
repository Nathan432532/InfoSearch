import Header from "./components/Header/Header";
import { Route, Routes, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import NotFound from "./pages/NotFoundPage";
import ChoicePage from "./pages/ChoicePage/ChoicePage";
import JobResultPage from "./pages/ResultPages/ResultPageJob";
import CompanyResultPage from "./pages/ResultPages/ResultPageCompany/CompanyResultPage";
import SearchPageJob from "./pages/SearchPages/SearchPageJob";
import SearchPageCompany from "./pages/SearchPages/SearchPageCompany/SearchPageCompany";
import SavedResultsPage from "./pages/SavedResultsPage/SavedResultsPage";
import LoginPage from "./pages/LoginPage/LoginPage";
import HomePage from "./pages/HomePage/HomePage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  if (loading) return null;

  return (
    <>
      {isAuthenticated && !isLoginPage && <Header />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to={isAuthenticated ? "/home" : "/login"} replace />} />
        <Route path="/home" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
        <Route path="/keuze" element={<ProtectedRoute><ChoicePage /></ProtectedRoute>} />
        <Route path="/search/job" element={<ProtectedRoute><SearchPageJob /></ProtectedRoute>} />
        <Route path="/search/company" element={<ProtectedRoute><SearchPageCompany /></ProtectedRoute>} />
        <Route path="/results/company" element={<ProtectedRoute><CompanyResultPage /></ProtectedRoute>} />
        <Route path="/results/job" element={<ProtectedRoute><JobResultPage /></ProtectedRoute>} />
        <Route path="/saved" element={<ProtectedRoute><SavedResultsPage /></ProtectedRoute>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}

export default App;