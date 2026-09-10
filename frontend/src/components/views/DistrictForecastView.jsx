import DistrictTable from '../tables/DistrictTable';
import RainfallMap from '../maps/RainfallMap';

export default function DistrictForecastView({ districts, setSelectedDistrict }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div className="lg:col-span-3 h-[520px]"><RainfallMap districts={districts} onDistrictClick={setSelectedDistrict} /></div>
        <div className="lg:col-span-2 h-[520px]"><DistrictTable districts={districts} onDistrictClick={setSelectedDistrict} /></div>
      </div>
    </div>
  );
}
