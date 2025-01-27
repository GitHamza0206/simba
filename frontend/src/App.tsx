import ChatFrame from '@/components/ChatFrame';
import ChatApp from '@/pages/ChatApp';
import DocumentManagementApp from "@/pages/DocumentManagementApp";
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/MainLayout';
import { pdfjs } from 'react-pdf';

// Use a direct path to the worker from node_modules
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<ChatApp />} />
        <Route path="/documents" element={<DocumentManagementApp />} />
        <Route path="*" element={<div className="p-8 text-center">Page Not Found</div>} />
      </Route>

      

    </Routes>
  );
}

export default App;
