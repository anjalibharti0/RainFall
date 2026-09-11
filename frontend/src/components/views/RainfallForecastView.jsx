import RainfallMap from '../maps/RainfallMap';
import TimeSeriesChart from '../charts/TimeSeriesChart';

export default function RainfallForecastView({ districts, setSelectedDistrict }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <div className="h-[700px]"><RainfallMap districts={districts} onDistrictClick={setSelectedDistrict} /></div>
      <TimeSeriesChart districts={districts} />
    </div>
  );
}
