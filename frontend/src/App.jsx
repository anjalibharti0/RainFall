import { useState, useEffect } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import RainfallMap from './components/maps/RainfallMap';
import ProbabilityMap from './components/maps/ProbabilityMap';
import VerificationChart from './components/charts/VerificationChart';
import TimeSeriesChart from './components/charts/TimeSeriesChart';
import LeadTimeChart from './components/charts/LeadTimeChart';
import RegimePieChart from './components/charts/RegimePieChart';
import DistrictTable from './components/tables/DistrictTable';
import VerificationPanel from './components/panels/VerificationPanel';
import RegimePanel from './components/panels/RegimePanel';
import AlertPanel from './components/panels/AlertPanel';
import { fetchForecast, fetchVerificationReport } from './services/api';

function App() {
  const [selectedDate, setSelectedDate] = useState('2026-09-09');
  const [leadTime, setLeadTime] = useState('24');
  const [activeView, setActiveView] = useState('overview');
  const [selectedDistrict, setSelectedDistrict] = useState(null);

  const [forecastData, setForecastData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [forecast, verification] = await Promise.all([
        fetchForecast(selectedDate, parseInt(leadTime)),
        fetchVerificationReport(selectedDate, parseInt(leadTime)),
      ]);
      setForecastData(forecast);
      setVerificationData(verification);
    } catch (err) {
      console.error('Data fetch error:', err);
      setError('Failed to connect to backend. Make sure the API server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDate, leadTime]);

  const regime = forecastData?.regime || null;
  const districts = forecastData?.districts || [];

  if (loading && !forecastData) {
    return (
      <div className="min-h-screen bg-[#f0f4f8] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[14px] font-semibold text-gray-500">Loading forecast data...</p>
          <p className="text-[12px] text-gray-400 mt-1">Connecting to ML backend</p>
        </div>
      </div>
    );
  }

  if (error && !forecastData) {
    return (
      <div className="min-h-screen bg-[#f0f4f8] flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-[18px] font-bold text-gray-900 mb-2">Backend Connection Error</h2>
          <p className="text-[13px] text-gray-500 mb-4">{error}</p>
          <p className="text-[12px] text-gray-400 mb-4">Run the backend server:</p>
          <code className="block bg-gray-50 rounded-lg p-3 text-[12px] font-mono text-gray-700 text-left">
            cd backend<br />
            python -m uvicorn main:app --port 8000 --reload
          </code>
          <button onClick={loadData} className="btn-primary mt-4">Retry Connection</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f0f4f8] grid-pattern">
      <Header
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        leadTime={leadTime}
        setLeadTime={setLeadTime}
        regime={regime}
        onRefresh={loadData}
        loading={loading}
      />

      <div className="flex flex-col lg:flex-row h-[calc(100vh-80px)]">
        <Sidebar
          activeView={activeView}
          setActiveView={setActiveView}
          regime={regime}
          districts={districts}
        />

        <main className="flex-1 overflow-y-auto p-5 lg:p-6">
          {activeView === 'overview' && (
            <div className="space-y-5 max-w-[1400px]">
              <RegimePanel regime={regime} />

              <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
                <div className="xl:col-span-2 h-[420px]">
                  <RainfallMap districts={districts} onDistrictClick={setSelectedDistrict} />
                </div>
                <div>
                  <AlertPanel districts={districts} />
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                <VerificationChart verification={verificationData} />
                <TimeSeriesChart />
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
                <div className="xl:col-span-2">
                  <DistrictTable districts={districts} onDistrictClick={setSelectedDistrict} />
                </div>
                <div>
                  <RegimePieChart districts={districts} />
                </div>
              </div>
            </div>
          )}

          {activeView === 'rainfall' && (
            <div className="space-y-5 max-w-[1400px]">
              <div className="h-[550px]">
                <RainfallMap districts={districts} onDistrictClick={setSelectedDistrict} />
              </div>
              <DistrictTable districts={districts} onDistrictClick={setSelectedDistrict} />
            </div>
          )}

          {activeView === 'probability' && (
            <div className="space-y-5 max-w-[1400px]">
              <div className="h-[550px]">
                <ProbabilityMap districts={districts} />
              </div>
              <AlertPanel districts={districts} />
            </div>
          )}

          {activeView === 'verification' && (
            <div className="space-y-5 max-w-[1400px]">
              <VerificationPanel verification={verificationData} />
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                <VerificationChart verification={verificationData} />
                <LeadTimeChart verification={verificationData} />
              </div>
              <TimeSeriesChart />
            </div>
          )}

          {/* District Detail Modal */}
          {selectedDistrict && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4" onClick={() => setSelectedDistrict(null)}>
              <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 relative border border-gray-100" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setSelectedDistrict(null)}
                  className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors text-lg font-medium"
                >
                  ×
                </button>

                <div className="mb-5">
                  <h2 className="text-[20px] font-extrabold text-gray-900 tracking-[-0.02em]">{selectedDistrict.name}</h2>
                  <p className="text-[13px] text-gray-400 mt-0.5">{selectedDistrict.state} · {selectedDistrict.zone?.replace('_', ' ')}</p>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-5">
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Raw NWP</div>
                    <div className="text-[22px] font-extrabold text-gray-700 tracking-[-0.02em]">{selectedDistrict.raw} <span className="text-[12px] font-medium text-gray-400">mm</span></div>
                  </div>
                  <div className="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100">
                    <div className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider mb-1">Corrected</div>
                    <div className="text-[22px] font-extrabold text-emerald-700 tracking-[-0.02em]">{selectedDistrict.corrected} <span className="text-[12px] font-medium text-emerald-500">mm</span></div>
                  </div>
                </div>

                <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">Exceedance Probabilities</div>
                <div className="space-y-3">
                  {[
                    { label: 'P(R > 7.5mm)', value: selectedDistrict.p_moderate || Math.min((selectedDistrict.p_heavy || 0) * 1.2, 0.98), color: '#0ea5e9' },
                    { label: 'P(R > 64.5mm)', value: selectedDistrict.p_heavy || 0, color: '#f59e0b' },
                    { label: 'P(R > 124.5mm)', value: selectedDistrict.p_very_heavy || 0, color: '#ef4444' },
                    { label: 'P(R > 244.5mm)', value: selectedDistrict.p_extreme || 0, color: '#dc2626' },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[12px] font-medium text-gray-500">{item.label}</span>
                        <span className="text-[13px] font-bold text-gray-800">{(item.value * 100).toFixed(1)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-bar-fill" style={{ width: `${item.value * 100}%`, backgroundColor: item.color }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
