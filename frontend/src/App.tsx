import ChatApp from '@/pages/ChatApp';
import DocumentManagementApp from "@/pages/DocumentManagementApp";
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/MainLayout';
import { pdfjs } from 'react-pdf';
import Login from '@/pages/auth/Login';
import Signup from '@/pages/auth/Signup';
import ResetPassword from '@/pages/auth/ResetPassword';
import { AuthProvider, ProtectedRoute } from '@/context/AuthContext';
import RolesPage from './pages/RolesPage';
import OrganizationPage from './pages/OrganizationPage';
import SettingsPage from './pages/SettingsPage';
import GeneralSettings from './pages/settings/GeneralSettings';
import MembersSettings from './pages/settings/MembersSettings';
import KnowledgeConfigPage from './pages/KnowledgeConfigPage';
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
          <Route path="/knowledge" element={
            <ProtectedRoute>
              <KnowledgeConfigPage />
            </ProtectedRoute>
          } />
          
          {/* Settings Routes */}
          <Route path="/settings" element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }>
            <Route index element={<GeneralSettings />} />
            <Route path="members" element={<MembersSettings />} />
            <Route path="billing" element={<div className="p-8">Billing settings coming soon</div>} />
            <Route path="sso" element={<div className="p-8">SSO settings coming soon</div>} />
            <Route path="projects" element={<div className="p-8">Projects settings coming soon</div>} />
            <Route path="roles" element={<RolesPage />} />
          </Route>
          
          {/* Legacy routes - redirect to the new settings structure */}
          <Route path="/roles" element={
            <ProtectedRoute>
              <Navigate to="/settings/roles" replace />
            </ProtectedRoute>
          } />
          <Route path="/organizations" element={
            <ProtectedRoute>
              <Navigate to="/settings" replace />
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
