import { Route, Routes } from "react-router-dom";
import Dashboard from "./pages/dashboard.jsx";
import Editor from "./pages/editor.jsx";
import Investigar from "./pages/investigar.jsx";

const ROUTE_PATHS = Object.freeze({
  dashboard: "/",
  editor: "/projeto/:projetoId/pasta/:pastaId",
    investigar: "/investigar",
});

export default function App() {
  return (
    <Routes>
      <Route path={ROUTE_PATHS.dashboard} element={<Dashboard />} />
      <Route path={ROUTE_PATHS.editor} element={<Editor />} />
        <Route path={ROUTE_PATHS.investigar} element={<Investigar />} />
    </Routes>
  );
}