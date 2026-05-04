import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";
import { AnnotatePage } from "./pages/AnnotatePage";
import { ViewerPage } from "./pages/ViewerPage";

function SetupRedirect(): JSX.Element {
  const params = new URLSearchParams(window.location.search);
  const pid = params.get("project_id");
  return <Navigate to={pid ? `/annotate?project_id=${pid}` : "/"} replace />;
}

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/setup" element={<SetupRedirect />} />
        <Route path="/annotate" element={<AnnotatePage />} />
        <Route path="/viewer" element={<ViewerPage />} />
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}
