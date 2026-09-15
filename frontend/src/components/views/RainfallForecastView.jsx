import RainfallMap from '../maps/RainfallMap';
import TimeSeriesChart from '../charts/TimeSeriesChart';

export default function RainfallForecastView({ districts, setSelectedDistrict }) {
  return (
    <div className="max-w-[1600px] mx-auto flex flex-col gap-5">
      <div className="sticky top-0 z-10 h-[60vh] min-h-[400px] animate-fade-slide-up delay-1">
        <RainfallMap districts={districts} onDistrictClick={setSelectedDistrict} />
      </div>
      <div className="relative z-0 animate-fade-slide-up delay-2">
        <TimeSeriesChart districts={districts} />
      </div>
    </div>
  );
}
