'use client';

import { useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function Home() {
  const [symbol, setSymbol] = useState('');
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchPriceHistory = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/price-history/${symbol}`);
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      const labels = data.map((item: any) => item.Date);
      const closePrices = data.map((item: any) => item.Close);
      setChartData({
        labels,
        datasets: [
          {
            label: `${symbol.toUpperCase()} Close Price`,
            data: closePrices,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
          },
        ],
      });
    } catch (error) {
      console.error(error);
      alert('Error fetching data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>PharmaWatch Price History</h1>
      <div>
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter stock symbol (e.g., AAPL)"
        />
        <button onClick={fetchPriceHistory} disabled={loading}>
          {loading ? 'Loading...' : 'Fetch Price History'}
        </button>
      </div>
      {chartData && (
        <div style={{ marginTop: '20px' }}>
          <Line data={chartData} />
        </div>
      )}
    </div>
  );
}
