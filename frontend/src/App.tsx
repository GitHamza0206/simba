import ChatApp from '@/pages/ChatApp';
import DocumentManagementApp from "@/pages/DocumentManagementApp";
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/MainLayout';
import { pdfjs } from 'react-pdf';
import Login from '@/pages/auth/Login';
import Signup from '@/pages/auth/Signup';
import ResetPassword from '@/pages/auth/ResetPassword';
import { AuthProvider, ProtectedRoute } from '@/context/AuthContext';
import RolesPage from './pages/RolesPage';
import OrganizationPage from './pages/OrganizationPage';
import { Toaster } from '@/components/ui/toaster';

// Use a direct path to the worker from node_modules
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/signup" element={<Signup />} />
        <Route path="/auth/reset-password" element={<ResetPassword />} />
        
        <Route element={<MainLayout />}>
          <Route path="/" element={
            <ProtectedRoute>
              <ChatApp />
            </ProtectedRoute>
          } />
          <Route path="/documents" element={
            <ProtectedRoute>
              <DocumentManagementApp />
            </ProtectedRoute>
          } />
          <Route path="roles" element={
            <ProtectedRoute>
              <RolesPage />
            </ProtectedRoute>
          } />
          <Route path="organizations" element={
            <ProtectedRoute>
              <OrganizationPage />
            </ProtectedRoute>
          } />
          <Route path="*" element={<div className="p-8 text-center">Page Not Found</div>} />
        </Route>
      </Routes>
      <Toaster />
    </AuthProvider>
  );
}

export default App;
