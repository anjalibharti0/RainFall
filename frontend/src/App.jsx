import { useState, useEffect } from 'react';
import { useTheme } from './context/ThemeContext';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import DarkIndiaMap from './components/maps/DarkIndiaMap';
import NotificationPanel from './components/notifications/NotificationPanel';
import RedAlertNotification from './components/notifications/RedAlertNotification';
import WorkflowVisualization from './components/notifications/WorkflowVisualization';
import RoleNotificationPanel from './components/notifications/RoleNotificationPanel';
import AlertStats from './components/notifications/AlertStats';
import SummaryStats from './components/SummaryStats';
import RegimePanel from './components/panels/RegimePanel';
import HeavyRainProbability from './components/HeavyRainProbability';
import DistrictTable from './components/tables/DistrictTable';
import VerificationPanel from './components/panels/VerificationPanel';
import TimeSeriesChart from './components/charts/TimeSeriesChart';
import RegimeBarChart from './components/charts/RegimeBarChart';
import { fetchForecast, fetchVerificationReport, fetchIMDWarnings } from './services/api';

function App() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [selectedDate, setSelectedDate] = useState('2026-09-10');
  const [leadTime, setLeadTime] = useState('24');
  const [activeView, setActiveView] = useState('notifications');
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [imdWarnings, setImdWarnings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('synthetic');
  const [notifOpen, setNotifOpen] = useState(false);
  const [redAlertOpen, setRedAlertOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      // Fetch forecast and verification in parallel
      const [forecast, verification] = await Promise.all([
        fetchForecast(selectedDate, parseInt(leadTime)).catch(() => null),
        fetchVerificationReport(selectedDate, parseInt(leadTime)).catch(() => null),
      ]);

      if (forecast) {
        setForecastData(forecast);
        setDataSource(forecast.districts?.[0]?.data_source || 'synthetic');
      }

      if (verification) {
        setVerificationData(verification);
      }

      // Fetch IMD real-time warnings (non-blocking)
      fetchIMDWarnings().then(data => {
        if (data?.districts) {
          setImdWarnings(data.districts);
          setDataSource('IMD_real_time');
        }
      }).catch(() => {});

    } catch (err) {
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [selectedDate, leadTime]);

  // Auto-show red alert demo after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => setRedAlertOpen(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  const regime = forecastData?.regime || null;
  const districts = forecastData?.districts || [];

  // Merge IMD warnings with forecast data if available
  const mergedDistricts = districts.map(d => {
    const imdWarning = imdWarnings.find(w => w.name === d.name);
    if (imdWarning) {
      return {
        ...d,
        imd_warning_level: imdWarning.imd_warning_level,
        imd_warning_color: imdWarning.imd_warning_color,
        imd_rainfall_actual: imdWarning.imd_rainfall_actual,
        data_source: 'IMD_real_time',
      };
    }
    return d;
  });

  if (loading && !forecastData) {
    return (
      <div className={`min-h-screen flex items-center justify-center transition-colors ${isDark ? 'bg-[#0a0e1a]' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className={`w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4 ${isDark ? 'border-cyan-400' : 'border-cyan-600'}`} />
          <p className={`text-[14px] font-semibold ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>Connecting to IMD & ML Backend...</p>
          <p className={`text-[12px] mt-1 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>Fetching real-time weather data</p>
        </div>
      </div>
    );
  }

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
        onNotifClick={() => setNotifOpen(true)}
        dataSource={dataSource}
      />
      <div className="flex h-[calc(100vh-72px)]">
        <Sidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="flex-1 overflow-y-auto p-5">
          {activeView === 'notifications' && (
            <div className="max-w-[1600px] mx-auto space-y-5">
              <AlertStats />
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
                <div className="lg:col-span-3 h-[520px]">
                  <DarkIndiaMap />
                </div>
                <div className="lg:col-span-2">
                  <RoleNotificationPanel />
                </div>
              </div>
              <WorkflowVisualization />
            </div>
          )}

          {activeView === 'dashboard' && (
            <div className="max-w-[1600px] mx-auto space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <div className="lg:col-span-2"><RegimePanel regime={regime} /></div>
                <div><SummaryStats /></div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
                <div className="lg:col-span-3 h-[480px]"><DarkIndiaMap /></div>
                <div className="lg:col-span-2"><DistrictTable districts={mergedDistricts} onDistrictClick={setSelectedDistrict} /></div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <div><HeavyRainProbability /></div>
                <div><TimeSeriesChart /></div>
                <div><VerificationPanel verification={verificationData} /></div>
              </div>
              <RegimeBarChart />
            </div>
          )}

          {activeView === 'rainfall' && (
            <div className="max-w-[1600px] mx-auto space-y-5">
              <div className="h-[600px]"><DarkIndiaMap /></div>
            </div>
          )}

          {activeView === 'verification' && (
            <div className="max-w-[1600px] mx-auto space-y-5">
              <VerificationPanel verification={verificationData} />
              <TimeSeriesChart />
            </div>
          )}
        </main>
      </div>

      <NotificationPanel isOpen={notifOpen} onClose={() => setNotifOpen(false)} />
      <RedAlertNotification isOpen={redAlertOpen} onClose={() => setRedAlertOpen(false)} />
    </div>
  );
}

export default App;
