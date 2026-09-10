import VerificationPanel from '../panels/VerificationPanel';
import TimeSeriesChart from '../charts/TimeSeriesChart';

export default function VerificationView({ verificationData, districts }) {
  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <VerificationPanel verification={verificationData} />
      <TimeSeriesChart districts={districts} />
    </div>
  );
}
