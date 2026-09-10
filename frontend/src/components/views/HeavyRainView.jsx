import ProbabilityMap from '../maps/ProbabilityMap';
import HeavyRainProbability from '../HeavyRainProbability';

export default function HeavyRainView({ districts }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <div className="h-[600px]"><ProbabilityMap districts={districts} /></div>
      <HeavyRainProbability districts={districts} />
    </div>
  );
}
