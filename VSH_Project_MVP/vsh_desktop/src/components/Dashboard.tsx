import React from 'react';

interface DashboardProps {
  summary?: {
    total?: number;
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
    top_risky_files?: Array<[string, number] | { file: string; count: number }>;
  };
}

function Dashboard({ summary }: DashboardProps) {
  const safe = summary || {};
  const total = safe.total || 0;
  const critical = safe.critical || 0;
  const high = safe.high || 0;
  const medium = safe.medium || 0;
  const low = safe.low || 0;
  const topRiskyFiles = (safe.top_risky_files || []).map((entry) =>
    Array.isArray(entry) ? { file: entry[0], count: entry[1] } : entry
  );

  const StatBox = ({ title, value, borderColor }: { title: string; value: number; borderColor: string }) => (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        padding: 10,
        borderRadius: 5,
        minWidth: 100,
        textAlign: 'center',
        backgroundColor: '#fff',
      }}
    >
      <h3 style={{ margin: '0 0 5px 0', fontSize: '14px', color: '#666' }}>{title}</h3>
      <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: borderColor }}>{value}</p>
    </div>
  );

  if (total === 0) {
    return (
      <div style={{ marginTop: 20, padding: 20, backgroundColor: '#f9f9f9', borderRadius: 8, border: '1px solid #ddd' }}>
        <h2>Dashboard</h2>
        <p style={{ color: '#666', marginTop: 10 }}>
          No scan results yet. Select a file or project and start a scan to populate the dashboard.
        </p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: 20 }}>
      <h2>Dashboard</h2>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatBox title="Total Findings" value={total} borderColor="#999" />
        <StatBox title="Critical" value={critical} borderColor="#d32f2f" />
        <StatBox title="High" value={high} borderColor="#f57c00" />
        <StatBox title="Medium" value={medium} borderColor="#fbc02d" />
        <StatBox title="Low" value={low} borderColor="#388e3c" />
      </div>

      {topRiskyFiles.length > 0 && (
        <div>
          <h3>Top Risky Files</h3>
          <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
            {topRiskyFiles.map(({ file, count }) => (
              <li
                key={file}
                style={{
                  padding: '8px',
                  backgroundColor: '#f5f5f5',
                  marginBottom: 5,
                  borderRadius: 4,
                  borderLeft: '4px solid #ff6b6b',
                  paddingLeft: 12,
                }}
              >
                <code>{file}</code>: <strong>{count}</strong> issue{count !== 1 ? 's' : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
