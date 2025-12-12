'use client';

import { useState } from 'react';
import { Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  CandlestickController,
  CandlestickElement
);

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
      const candlestickData = data.map((item: any) => ({
        x: new Date(item.Date).getTime(),
        o: item.Open,
        h: item.High,
        l: item.Low,
        c: item.Close,
      }));
      setChartData({
        datasets: [
          {
            label: `${symbol.toUpperCase()} Price`,
            data: candlestickData,
            color: {
              up: 'green',
              down: 'red',
              unchanged: 'gray',
            },
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

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol.toUpperCase()} Candlestick Chart`,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day' as const,
        },
      },
    },
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
          <Chart type="candlestick" data={chartData} options={options} />
        </div>
      )}
    </div>
  );
}
