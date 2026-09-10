import { useState } from 'react';

export default function DistrictTable({ districts, onDistrictClick }) {
  const [sortKey, setSortKey] = useState('corrected');
  const [sortDir, setSortDir] = useState('desc');
  const [search, setSearch] = useState('');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = [...districts]
    .filter(d => !search || d.name.toLowerCase().includes(search.toLowerCase()) || d.state.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const va = a[sortKey] || 0;
      const vb = b[sortKey] || 0;
      return sortDir === 'asc' ? va - vb : vb - va;
    });

  const SortHeader = ({ label, field }) => (
    <th
      className="cursor-pointer hover:text-gray-700 select-none"
      onClick={() => handleSort(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        {sortKey === field && <span className="text-gray-300">{sortDir === 'asc' ? '↑' : '↓'}</span>}
      </span>
    </th>
  );

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">District Forecasts</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">{sorted.length} districts · Click row for details</p>
        </div>
        <input
          type="text"
          placeholder="Search district or state..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field w-[200px] text-[12px]"
        />
      </div>
      <div className="overflow-auto max-h-[400px]">
        <table className="data-table w-full">
          <thead className="sticky top-0 bg-white">
            <tr>
              <SortHeader label="District" field="name" />
              <SortHeader label="State" field="state" />
              <SortHeader label="Raw (mm)" field="raw" />
              <SortHeader label="Corrected (mm)" field="corrected" />
              <SortHeader label="Regime" field="regime" />
              <SortHeader label="P(Heavy)" field="p_heavy" />
              <SortHeader label="P(Very Heavy)" field="p_very_heavy" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((d) => (
              <tr
                key={d.district_id}
                className="cursor-pointer hover:bg-sky-50/50"
                onClick={() => onDistrictClick?.(d)}
              >
                <td className="font-semibold text-gray-900">{d.name}</td>
                <td className="text-gray-500">{d.state}</td>
                <td className="font-medium text-gray-600">{d.raw}</td>
                <td>
                  <span className={`font-bold ${d.corrected > 64.5 ? 'text-red-600' : d.corrected > 35 ? 'text-amber-600' : 'text-sky-600'}`}>
                    {d.corrected}
                  </span>
                </td>
                <td>
                  <span className="capitalize text-[12px] text-gray-500">{(d.regime || '').replace('_', ' ')}</span>
                </td>
                <td>
                  <span className={`font-semibold ${(d.p_heavy || 0) > 0.5 ? 'text-amber-600' : 'text-gray-600'}`}>
                    {((d.p_heavy || 0) * 100).toFixed(0)}%
                  </span>
                </td>
                <td>
                  <span className={`font-semibold ${(d.p_very_heavy || 0) > 0.3 ? 'text-red-500' : 'text-gray-600'}`}>
                    {((d.p_very_heavy || 0) * 100).toFixed(0)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
