import PropTypes from 'prop-types';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import AirQualityPage from './pages/AirQualityPage';
import FactoriesPage from './pages/FactoriesPage';
import SensorsPage from './pages/SensorsPage';
import AlertsPage from './pages/AlertsPage';
import MapPage from './pages/MapPage';
import FactoryDetailPage from './pages/FactoryDetailPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import NotFoundPage from './pages/NotFoundPage';
import DataSourcesPage from './pages/DataSourcesPage';
import useAuthStore from './store/authStore';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected routes with layout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="air-quality" element={<AirQualityPage />} />
          <Route path="factories" element={<FactoriesPage />} />
          <Route path="factories/:factoryId" element={<FactoryDetailPage />} />
          <Route path="sensors" element={<SensorsPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="map" element={<MapPage />} />
          <Route path="data-sources" element={<DataSourcesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
