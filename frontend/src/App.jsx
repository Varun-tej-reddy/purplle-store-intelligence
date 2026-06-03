import { useEffect, useMemo, useState } from 'react';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { getAnomalies, getFunnel, getHealth, getHeatmap, getMetrics } from './api';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

const STORE_ID = 'store_1';
const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  resizeDelay: 200
};

function StatCard({ label, value }) {
  return (
    <article className="card stat-card">
      <p>{label}</p>
      <h2>{value}</h2>
    </article>
  );
}

function App() {
  const [metrics, setMetrics] = useState(null);
  const [funnel, setFunnel] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        const [m, f, h, a, hl] = await Promise.all([
          getMetrics(STORE_ID),
          getFunnel(STORE_ID),
          getHeatmap(STORE_ID),
          getAnomalies(STORE_ID),
          getHealth()
        ]);

        if (!isMounted) return;
        setMetrics(m);
        setFunnel(f.stages || []);
        setHeatmap(h.zones || []);
        setAnomalies(a.active_anomalies || []);
        setHealth(hl);
        setError(null);
      } catch (err) {
        if (!isMounted) return;
        setError(err.message);
      }
    }

    // Poller is created once and cleaned up on unmount to avoid interval leaks.
    loadData();
    const id = setInterval(loadData, 15000);
    return () => {
      isMounted = false;
      clearInterval(id);
    };
  }, []);

  const funnelChartData = useMemo(
    () => ({
      labels: funnel.map((s) => s.stage),
      datasets: [
        {
          label: 'Visitors',
          data: funnel.map((s) => s.count),
          backgroundColor: ['#244855', '#3f7d58', '#8bc34a', '#f8b400']
        }
      ]
    }),
    [funnel]
  );

  const conversionChartData = useMemo(
    () => ({
      labels: ['Converted', 'Not Converted'],
      datasets: [
        {
          data: metrics
            ? [
                Number((metrics.conversion_rate * 100).toFixed(2)),
                Number((100 - metrics.conversion_rate * 100).toFixed(2))
              ]
            : [0, 100],
          backgroundColor: ['#2e7d32', '#d6d6d6'],
          borderWidth: 0
        }
      ]
    }),
    [metrics]
  );

  return (
    <div className="app-shell">
      <header>
        <h1>Purplle Store Intelligence</h1>
        <p>Live analytics from CCTV-powered visitor events</p>
      </header>

      {error && <div className="alert error">{error}</div>}

      <section className="stats-grid">
        <StatCard label="Visitor Count" value={metrics?.unique_visitors ?? '-'} />
        <StatCard
          label="Conversion Rate"
          value={metrics ? `${(metrics.conversion_rate * 100).toFixed(2)}%` : '-'}
        />
        <StatCard label="Queue Depth" value={metrics?.queue_depth ?? '-'} />
        <StatCard
          label="Abandonment Rate"
          value={metrics ? `${(metrics.abandonment_rate * 100).toFixed(2)}%` : '-'}
        />
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <h3>Funnel Chart</h3>
          {/* Fixed container + stable options prevents resize feedback loops that can grow card height over time. */}
          <div className="chart-container">
            <Bar data={funnelChartData} options={CHART_OPTIONS} />
          </div>
        </article>

        <article className="card">
          <h3>Conversion Snapshot</h3>
          <div className="chart-container doughnut-wrap">
            <Doughnut data={conversionChartData} options={CHART_OPTIONS} />
          </div>
        </article>

        <article className="card span-2">
          <h3>Heatmap Table</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Zone</th>
                  <th>Visits</th>
                  <th>Average Dwell (ms)</th>
                  <th>Normalized Score</th>
                </tr>
              </thead>
              <tbody>
                {heatmap.map((row) => (
                  <tr key={row.zone}>
                    <td>{row.zone}</td>
                    <td>{row.visits}</td>
                    <td>{row.average_dwell}</td>
                    <td>{row.normalized_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="card">
          <h3>Anomaly Alerts</h3>
          <ul className="feed-list">
            {anomalies.length === 0 && <li>No active anomalies</li>}
            {anomalies.map((a, idx) => (
              <li key={`${a.anomaly_type}-${idx}`}>
                <strong>{a.anomaly_type}</strong> [{a.severity}]<br />
                <span>{a.message}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h3>Live Event Feed</h3>
          <ul className="feed-list">
            <li>Status: {health?.status ?? '-'}</li>
            <li>Last Event: {health?.last_event_timestamp ?? '-'}</li>
            <li>Stale Warning: {health?.stale_feed_warning ? 'Yes' : 'No'}</li>
          </ul>
        </article>
      </section>
    </div>
  );
}

export default App;
