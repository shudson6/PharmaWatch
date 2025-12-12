'use client';

import { useState, useRef } from 'react';
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
  const [catalystMap, setCatalystMap] = useState<any>({});
  const [selectedSummaries, setSelectedSummaries] = useState<string[]>([]);
  const chartRef = useRef<any>();

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
      const catalystMap = articles.reduce((acc: any, article: any) => {
        const dateStr = new Date(article.date).toISOString().split('T')[0];
        if (!acc[dateStr]) acc[dateStr] = { sentiments: [], titles: [], summaries: [] };
        acc[dateStr].sentiments.push(article.sentiment);
        acc[dateStr].titles.push(article.title);
        acc[dateStr].summaries.push(article.summary);
        return acc;
      }, {});
      const catalystDates = Object.keys(catalystMap).map(d => new Date(d));
      setCatalysts(catalystDates);
      setCatalystMap(catalystMap);
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

  const handleClick = (event: any, elements: any) => {
    console.log('handleClick called', event, elements);
    const chart = chartRef.current;
    if (!chart) {
      console.log('no chart ref');
      return;
    }
    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const xScale = chart.scales.x;
    if (x < xScale.left || x > xScale.right) {
      console.log('Click outside x scale area');
      return;
    }
    const xValue = xScale.getValueForPixel(x);
    console.log('xValue:', xValue, 'x:', x, 'event.clientX:', event.clientX, 'rect.left:', rect.left);
    if (isNaN(xValue)) return;
    const clickDate = new Date(xValue);
    if (isNaN(clickDate.getTime())) return;
    const clickDateStr = clickDate.toISOString().split('T')[0];
    console.log('Click xValue:', xValue, 'clickDateStr:', clickDateStr);
    // find the catalyst date closest to clickDate
    const catalystDates = Object.keys(catalystMap);
    let closest = null;
    let minDiff = Infinity;
    for (const d of catalystDates) {
      const diff = Math.abs(new Date(d).getTime() - clickDate.getTime());
      if (diff < minDiff) {
        minDiff = diff;
        closest = d;
      }
    }
    if (closest && minDiff < 24 * 60 * 60 * 1000) { // within 1 day
      console.log('Closest catalyst:', closest, 'Summaries:', catalystMap[closest].summaries);
      setSelectedSummaries(catalystMap[closest].summaries.filter((s: any) => s));
    } else {
      console.log('No close catalyst found');
      setSelectedSummaries([]);
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
      tooltip: {
        callbacks: {
          footer: (context: any) => {
            const date = new Date(context[0].parsed.x);
            const dateStr = date.toISOString().split('T')[0];
            const data = catalystMap[dateStr];
            if (data && data.titles.length > 0) {
              return 'News: ' + data.titles.slice(0, 3).join('; ');
            }
            return '';
          },
        },
      },
      annotation: {
        annotations: Object.entries(catalystMap).reduce((acc: any, [dateStr, data]: [string, any], index: number) => {
          const date = new Date(dateStr);
          const { sentiments, titles } = data;
          const hasPositive = sentiments.some((s: string) => s && s.toLowerCase() === 'positive');
          const hasNegative = sentiments.some((s: string) => s && s.toLowerCase() === 'negative');
          const color = hasPositive ? 'green' : hasNegative ? 'red' : 'orange';
          acc[`catalyst-${index}`] = {
            type: 'line' as const,
            xMin: date.getTime(),
            xMax: date.getTime(),
            borderColor: color,
            borderWidth: 2,
            label: {
              content: titles.slice(0, 3).join('\n'), // Show up to 3 titles
              enabled: true,
              position: 'center',
              backgroundColor: 'rgba(0,0,0,0.8)',
              color: 'white',
              font: {
                size: 12,
              },
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
          <Chart ref={chartRef} type="candlestick" data={chartData} options={options} onClick={handleClick} />
        </div>
      )}
      {selectedSummaries.length > 0 && (
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #fff', backgroundColor: '#000', color: '#fff' }}>
          <h3>Article Summaries</h3>
          {selectedSummaries.map((summary, idx) => (
            <p key={idx}>{summary}</p>
          ))}
        </div>
      )}
    </div>
  );
}
