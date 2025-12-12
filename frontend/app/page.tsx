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
  BarController,
  BarElement,
} from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-luxon';
import annotationPlugin from 'chartjs-plugin-annotation';

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
  CandlestickElement,
  BarController,
  BarElement,
  annotationPlugin
);

export default function Home() {
  const [symbol, setSymbol] = useState('');
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [catalysts, setCatalysts] = useState<Date[]>([]);

  const fetchPriceHistory = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const [priceResponse, articlesResponse] = await Promise.all([
        fetch(`/api/price-history/${symbol}`),
        fetch(`/api/articles/${symbol}`),
      ]);
      if (!priceResponse.ok || !articlesResponse.ok) throw new Error('Failed to fetch');
      const data = await priceResponse.json();
      const articles = await articlesResponse.json();
      const catalystDates = [...new Set(articles.map((a: any) => a.date))].map((d: any) => new Date(d));
      setCatalysts(catalystDates);
      const candlestickData = data.map((item: any) => ({
        x: new Date(item.Date).getTime(),
        o: item.Open,
        h: item.High,
        l: item.Low,
        c: item.Close,
      }));
      const volumeData = data.map((item: any) => ({
        x: new Date(item.Date).getTime(),
        y: item.Volume,
      }));
      setChartData({
        datasets: [
          {
            label: `${symbol.toUpperCase()} Price`,
            data: candlestickData,
            yAxisID: 'y',
            color: {
              up: 'green',
              down: 'red',
              unchanged: 'gray',
            },
          },
          {
            label: `${symbol.toUpperCase()} Volume`,
            data: volumeData,
            type: 'bar' as const,
            yAxisID: 'volume',
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
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
      annotation: {
        annotations: catalysts.reduce((acc: any, date: Date, index: number) => {
          acc[`catalyst-${index}`] = {
            type: 'line' as const,
            xMin: date.getTime(),
            xMax: date.getTime(),
            borderColor: 'orange',
            borderWidth: 2,
            label: {
              content: 'Catalyst',
              enabled: true,
              position: 'top',
            },
          };
          return acc;
        }, {}),
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day' as const,
        },
      },
      y: {
        type: 'linear' as const,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Price',
        },
      },
      volume: {
        type: 'linear' as const,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Volume',
        },
        grid: {
          drawOnChartArea: false,
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
