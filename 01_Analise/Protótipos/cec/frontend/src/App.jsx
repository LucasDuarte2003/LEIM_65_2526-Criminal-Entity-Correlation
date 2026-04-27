import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Editor from "./pages/Editor";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projeto/:projetoId/pasta/:pastaId" element={<Editor />} />
      </Routes>
    </BrowserRouter>
  );
}