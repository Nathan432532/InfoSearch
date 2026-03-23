import Header from "./components/Header/Header";
import { Route, Routes, Navigate } from "react-router-dom";
import NotFound from "./pages/NotFoundPage";
import ChoicePage from "./pages/ChoicePage/ChoicePage";
import JobResultPage from "./pages/ResultPages/ResultPageJob";
import CompanyResultPage from "./pages/ResultPages/ResultPageCompany/CompanyResultPage";
import SearchPageJob from "./pages/SearchPages/SearchPageJob";
import SearchPageCompany from "./pages/SearchPages/SearchPageCompany/SearchPageCompany";
import SavedResultsPage from "./pages/SavedResultsPage/SavedResultsPage";


function App() {
  return (
    <>
      <Header userName="Jan Janssen"/>
      <Routes>
        <Route path="/" element={<Navigate to="/keuze" replace />} />
        <Route path="/keuze" element={<ChoicePage />} />
        <Route path="/search/job" element={<SearchPageJob />} />
        <Route path="/search/company" element={<SearchPageCompany />} />
        <Route path="/results/company" element={<CompanyResultPage />} />
        <Route path="/results/job" element={<JobResultPage />} />
        <Route path="/saved" element={<SavedResultsPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}

export default App;