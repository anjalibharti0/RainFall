import VerificationPanel from '../panels/VerificationPanel';
import TimeSeriesChart from '../charts/TimeSeriesChart';

export default function VerificationView({ verificationData, districts }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <div className="animate-fade-slide-up delay-1">
        <VerificationPanel verification={verificationData} />
      </div>
      <div className="animate-fade-slide-up delay-2">
        <TimeSeriesChart districts={districts} />
      </div>
    </div>
  );
}
