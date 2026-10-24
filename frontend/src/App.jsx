import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Report from "./pages/Report";
import ReportById from "./pages/ReportById";
import History from "./pages/History";
import Docs from "./pages/Docs";
import Privacy from "./pages/Privacy";

export default function App() {
  return (
    <>
      <Nav />
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/report" element={<Report />} />
          <Route path="/report/:id" element={<ReportById />} />
          <Route path="/history" element={<History />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/privacy" element={<Privacy />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
