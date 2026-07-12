"use client";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Stock {
  ticker: string;
  close: number;
  signal: string;
  signal_score: number;
  confidence: number;
  rsi: number;
  macd: number;
  bb_position: number;
  momentum_7d: number;
  volume_ratio: number;
  predicted_price: number;
  predicted_change_pct: number;
  mae: number;
}

interface SignalsData {
  generated_at: string;
  market_status: string;
  total_stocks: number;
  stocks: Stock[];
}

interface Summary {
  buy: string[];
  sell: string[];
  hold: string[];
  high_volatility_alert: string[];
  market_status: string;
}

const signalColor = (signal: string) => {
  if (signal.includes("STRONG BUY")) return "text-green-400 bg-green-400/10 border-green-400/30";
  if (signal.includes("BUY")) return "text-green-400 bg-green-400/10 border-green-400/30";
  if (signal.includes("STRONG SELL")) return "text-red-400 bg-red-400/10 border-red-400/30";
  if (signal.includes("SELL")) return "text-red-400 bg-red-400/10 border-red-400/30";
  return "text-yellow-400 bg-yellow-400/10 border-yellow-400/30";
};

const marketStatusColor = (status: string) => {
  if (status === "OPEN") return "text-green-400";
  if (status === "PRE-MARKET") return "text-blue-400";
  if (status === "AFTER-HOURS") return "text-purple-400";
  return "text-gray-400";
};

const RSIBar = ({ value }: { value: number }) => {
  const color = value > 70 ? "bg-red-400" : value < 30 ? "bg-green-400" : "bg-yellow-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-400">{value.toFixed(1)}</span>
    </div>
  );
};

export default function Home() {
  const [data, setData] = useState<SignalsData | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchData = async () => {
    try {
      const [signalsRes, summaryRes] = await Promise.all([
        fetch(`${API_URL}/signals`),
        fetch(`${API_URL}/summary`)
      ]);
      const signalsData = await signalsRes.json();
      const summaryData = await summaryRes.json();
      setData(signalsData);
      setSummary(summaryData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      console.error("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔔</div>
          <div className="text-white text-xl">Loading OpenBell...</div>
          <div className="text-gray-400 text-sm mt-2">Fetching pre-market intelligence</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">🔔 OpenBell</h1>
            <p className="text-gray-400 text-sm">Pre-market stock intelligence — rings before the market does</p>
          </div>
          <div className="text-right">
            <div className={`text-lg font-semibold ${marketStatusColor(data?.market_status || "")}`}>
              ● {data?.market_status}
            </div>
            <div className="text-gray-400 text-xs">Updated: {lastUpdated}</div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-[#161b22] border border-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-xs mb-1">BUY Signals</div>
              <div className="text-2xl font-bold text-green-400">{summary.buy.length}</div>
              <div className="text-xs text-gray-500">{summary.buy.join(", ") || "None"}</div>
            </div>
            <div className="bg-[#161b22] border border-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-xs mb-1">SELL Signals</div>
              <div className="text-2xl font-bold text-red-400">{summary.sell.length}</div>
              <div className="text-xs text-gray-500">{summary.sell.join(", ") || "None"}</div>
            </div>
            <div className="bg-[#161b22] border border-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-xs mb-1">HOLD Signals</div>
              <div className="text-2xl font-bold text-yellow-400">{summary.hold.length}</div>
              <div className="text-xs text-gray-500">{summary.hold.join(", ") || "None"}</div>
            </div>
            <div className="bg-[#161b22] border border-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-xs mb-1">Volatility Alert</div>
              <div className="text-2xl font-bold text-orange-400">{summary.high_volatility_alert.length}</div>
              <div className="text-xs text-gray-500">{summary.high_volatility_alert.join(", ") || "None"}</div>
            </div>
          </div>
        )}

        {/* Pipeline Info Banner */}
        <div className="bg-[#161b22] border border-blue-500/20 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-blue-400 font-semibold text-sm">⚡ Powered by Hadoop MapReduce</span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-gray-400">
            <span className="bg-gray-800 px-2 py-1 rounded">Yahoo Finance → HDFS</span>
            <span className="text-gray-600">→</span>
            <span className="bg-gray-800 px-2 py-1 rounded">Hadoop Streaming MapReduce</span>
            <span className="text-gray-600">→</span>
            <span className="bg-gray-800 px-2 py-1 rounded">RF + GB Ensemble ML</span>
            <span className="text-gray-600">→</span>
            <span className="bg-gray-800 px-2 py-1 rounded">Pre-Market Signals</span>
          </div>
        </div>

        {/* Stock Table */}
        <div className="bg-[#161b22] border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h2 className="font-semibold text-gray-200">Pre-Market Intelligence — {data?.total_stocks} Stocks</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 text-xs">
                  <th className="px-4 py-3 text-left">Stock</th>
                  <th className="px-4 py-3 text-right">Price</th>
                  <th className="px-4 py-3 text-right">Predicted</th>
                  <th className="px-4 py-3 text-right">Change</th>
                  <th className="px-4 py-3 text-center">Signal</th>
                  <th className="px-4 py-3 text-center">Confidence</th>
                  <th className="px-4 py-3 text-left">RSI</th>
                  <th className="px-4 py-3 text-right">7d Mom</th>
                  <th className="px-4 py-3 text-right">MAE</th>
                </tr>
              </thead>
              <tbody>
                {data?.stocks.map((stock) => (
                  <tr key={stock.ticker} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                    <td className="px-4 py-3 font-bold text-white">{stock.ticker}</td>
                    <td className="px-4 py-3 text-right font-mono">${stock.close.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono text-gray-300">${stock.predicted_price.toFixed(2)}</td>
                    <td className={`px-4 py-3 text-right font-mono ${stock.predicted_change_pct > 0 ? "text-green-400" : "text-red-400"}`}>
                      {stock.predicted_change_pct > 0 ? "▲" : "▼"} {Math.abs(stock.predicted_change_pct).toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded border text-xs font-medium ${signalColor(stock.signal)}`}>
                        {stock.signal}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <div className="w-12 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-400 rounded-full" style={{ width: `${stock.confidence}%` }} />
                        </div>
                        <span className="text-xs text-gray-400">{stock.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3"><RSIBar value={stock.rsi} /></td>
                    <td className={`px-4 py-3 text-right text-xs ${stock.momentum_7d > 0 ? "text-green-400" : "text-red-400"}`}>
                      {stock.momentum_7d > 0 ? "+" : ""}{stock.momentum_7d.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-gray-400">${stock.mae.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-gray-600">
          <p>OpenBell — Pre-market intelligence powered by Hadoop HDFS + MapReduce + scikit-learn</p>
          <p className="mt-1">Not financial advice. For educational purposes only.</p>
        </div>
      </main>
    </div>
  );
}
