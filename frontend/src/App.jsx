import { useState, useEffect, useRef } from 'react';
import { useTheme } from './context/ThemeContext';
import { useNotification } from './hooks/useNotification';
import { analyzeForecastData, analyzeApiError } from './services/alertEngine';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import DashboardView from './components/views/DashboardView';
import RegimeAnalysisView from './components/views/RegimeAnalysisView';
import RainfallForecastView from './components/views/RainfallForecastView';
import HeavyRainView from './components/views/HeavyRainView';
import DistrictForecastView from './components/views/DistrictForecastView';
import VerificationView from './components/views/VerificationView';
import SettingsView from './components/views/SettingsView';
import DistrictDetailModal from './components/common/DistrictDetailModal';
import NotificationContainer from './components/common/NotificationContainer';
import AlertBanner from './components/common/AlertBanner';
import { fetchForecast, fetchVerificationReport } from './services/api';
import { requestNotificationPermission } from './services/browserNotification';

export default function App() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { fire } = useNotification();
  const [selectedDate, setSelectedDate] = useState('2026-09-10');
  const [leadTime, setLeadTime] = useState('24');
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const prevForecastRef = useRef(null);

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [forecast, verification] = await Promise.all([
        fetchForecast(selectedDate, parseInt(leadTime)).catch(() => null),
        fetchVerificationReport(selectedDate, parseInt(leadTime)).catch(() => null),
      ]);

      if (forecast) {
        const alerts = analyzeForecastData(forecast, prevForecastRef.current);
        alerts.forEach((alert) => fire({ ...alert, sound: true, browser: true }));
        prevForecastRef.current = forecast;
        setForecastData(forecast);
      }

      if (verification) setVerificationData(verification);
    } catch (err) {
      console.error('Data fetch error:', err);
      const errorAlert = analyzeApiError(err);
      if (errorAlert) fire({ ...errorAlert, sound: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [selectedDate, leadTime]);

  const regime = forecastData?.regime || null;
  const districts = forecastData?.districts || [];

  if (loading && !forecastData) {
    return (
      <div className={`min-h-screen flex items-center justify-center transition-colors ${isDark ? 'bg-[#0a0e1a]' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className={`w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4 ${isDark ? 'border-cyan-400' : 'border-cyan-600'}`} />
          <p className={`text-[14px] font-semibold ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>Connecting to ML Backend...</p>
          <p className={`text-[12px] mt-1 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>Loading forecast data</p>
        </div>
      </div>
    );
  }

  const viewProps = { forecastData, verificationData, regime, districts, loading, selectedDate, leadTime, setSelectedDistrict };

  return (
    <div className={`min-h-screen transition-colors ${isDark ? 'bg-meteorological' : 'bg-gray-50'}`}>
      <Header
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        leadTime={leadTime}
        setLeadTime={setLeadTime}
        regime={regime}
        onRefresh={loadData}
        loading={loading}
      />
      <AlertBanner />
      <div className="flex h-[calc(100vh-72px)]">
        <Sidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="flex-1 overflow-y-auto p-5">
          {activeView === 'dashboard' && <DashboardView {...viewProps} />}
          {activeView === 'regime' && <RegimeAnalysisView {...viewProps} />}
          {activeView === 'rainfall' && <RainfallForecastView {...viewProps} />}
          {activeView === 'probability' && <HeavyRainView {...viewProps} />}
          {activeView === 'district' && <DistrictForecastView {...viewProps} />}
          {activeView === 'verification' && <VerificationView {...viewProps} />}
          {activeView === 'settings' && <SettingsView />}
        </main>
      </div>
      {selectedDistrict && (
        <DistrictDetailModal district={selectedDistrict} onClose={() => setSelectedDistrict(null)} />
      )}
      <NotificationContainer />
    </div>
  );
}
