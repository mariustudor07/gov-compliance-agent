import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Report from "./pages/Report";
import ReportById from "./pages/ReportById";
import History from "./pages/History";
import Docs from "./pages/Docs";

export default function App() {
  return (
    <>
      <div className="bg-aurora" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
      <div className="bg-shapes-wrap" aria-hidden="true">
        <div className="bg-shapes" />
      </div>
      <Nav />
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/report" element={<Report />} />
          <Route path="/report/:id" element={<ReportById />} />
          <Route path="/history" element={<History />} />
          <Route path="/docs" element={<Docs />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
