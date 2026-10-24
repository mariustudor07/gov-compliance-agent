import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Report from "./pages/Report";
import ReportById from "./pages/ReportById";
import History from "./pages/History";
import Docs from "./pages/Docs";
import Privacy from "./pages/Privacy";
import Cookies from "./pages/Cookies";
import Accessibility from "./pages/Accessibility";

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
          <Route path="/cookies" element={<Cookies />} />
          <Route path="/accessibility" element={<Accessibility />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
