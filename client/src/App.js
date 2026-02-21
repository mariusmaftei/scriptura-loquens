import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import Header from "./components/Header/Header";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import ScripturePage from "./pages/ScripturePage";
import ProcessedDocumentsPage from "./pages/ProcessedDocumentsPage";
import EditAudioPage from "./pages/EditAudioPage";
import EditAudioStudioPage from "./pages/EditAudioStudioPage";
import AnalyzeJsonPage from "./pages/AnalyzeJsonPage";
import "./App.css";

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="App">
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/import" element={<UploadPage />} />
            <Route path="/biblioteca" element={<ProcessedDocumentsPage />} />
            <Route path="/post-productie" element={<EditAudioPage />} />
            <Route path="/post-productie/:pdfId" element={<EditAudioPage />} />
            <Route path="/post-productie/studio/:pdfId" element={<EditAudioStudioPage />} />
            <Route path="/documents/:pdfId" element={<ScripturePage />} />
            <Route path="/analizeaza" element={<AnalyzeJsonPage />} />
          </Routes>
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;
