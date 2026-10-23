import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Home from "./pages/Home";
import Report from "./pages/Report";
import ReportById from "./pages/ReportById";
import History from "./pages/History";

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
        </Routes>
      </main>
    </>
  );
}
