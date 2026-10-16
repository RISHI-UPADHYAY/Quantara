import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import OrganizationGate from './components/auth/OrganizationGate';

import Landing from "./features/Landing/Landing";
import Login from './features/Auth/Login';
import Register from './features/Auth/Register';
import Dashboard from './features/Dashboard/Dashboard';
import SubscriptionSelection from './features/Onboarding/SubscriptionSelection';
import CreateWorkspace from './features/Onboarding/CreateWorkspace';


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route element={<ProtectedRoute />}>
            <Route 
              path="/subscriptions" 
              element={<SubscriptionSelection />} 
            />
            
            <Route 
              path="/workspace/create" 
              element={<CreateWorkspace />} 
            />
            
            <Route 
              path="/dashboard" 
              element={
                <OrganizationGate>
                  <Dashboard />
                </OrganizationGate>
              } 
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App;