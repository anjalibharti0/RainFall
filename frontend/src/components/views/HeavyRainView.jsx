import ProbabilityMap from '../maps/ProbabilityMap';
import HeavyRainProbability from '../HeavyRainProbability';

export default function HeavyRainView({ districts }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <div className="h-[600px] animate-fade-slide-up delay-1"><ProbabilityMap districts={districts} /></div>
      <div className="animate-fade-slide-up delay-2"><HeavyRainProbability districts={districts} /></div>
    </div>
  );
}
