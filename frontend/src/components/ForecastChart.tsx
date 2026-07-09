import React, { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export interface ForecastChartProps {
  forecastData?: {
    ward_id: string;
    points: {
      timestamp: string;
      predicted_aqi: number;
      trend: string;
      lower?: number;
      upper?: number;
    }[];
  } | null;
  loading?: boolean;
}

const ForecastChartPresentational = ({ forecastData = null, loading = false }: ForecastChartProps) => {
  if (loading || !forecastData) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-4 animate-pulse">
        <div className="h-4 w-1/3 bg-slate-800 rounded" />
        <div className="h-48 bg-slate-800 rounded-lg" />
      </div>
    );
  }

  // Format the timestamp for X-Axis display (e.g. "09:00 AM")
  const chartData = useMemo(() => {
    if (!forecastData.points) return [];
    return forecastData.points.map((p) => {
      const date = new Date(p.timestamp);
      const timeStr = date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
      return {
        time: timeStr,
        AQI: p.predicted_aqi,
        Lower: p.lower ?? p.predicted_aqi - 20,
        Upper: p.upper ?? p.predicted_aqi + 20,
      };
    });
  }, [forecastData]);

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-4 text-white font-sans">
      <div className="flex justify-between items-center border-b border-[#334155] pb-3">
        <h4 className="text-[11px] font-bold text-[#bbc9cd] tracking-wider uppercase">
          AI AQI Prediction (Next 24h)
        </h4>
        <span className="text-xs text-[#22d3ee] font-semibold">
          Model: Prophet
        </span>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 5, left: -25, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#94A3B8"
              fontSize={10}
              tickLine={false}
            />
            <YAxis
              stroke="#94A3B8"
              fontSize={10}
              tickLine={false}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0F172A",
                borderColor: "#334155",
                borderRadius: "8px",
                color: "#F8FAFC",
                fontSize: "11px",
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "10px", color: "#bbc9cd" }}
              iconSize={8}
            />
            {/* Upper Bound Line */}
            <Line
              name="Upper Bound"
              type="monotone"
              dataKey="Upper"
              stroke="#22d3ee"
              strokeDasharray="3 3"
              strokeWidth={1}
              dot={false}
              opacity={0.4}
            />
            {/* Forecast Line */}
            <Line
              name="Predicted AQI"
              type="monotone"
              dataKey="AQI"
              stroke="#22d3ee"
              strokeWidth={2}
              dot={{ r: 3, fill: "#22d3ee" }}
              activeDot={{ r: 5 }}
            />
            {/* Lower Bound Line */}
            <Line
              name="Lower Bound"
              type="monotone"
              dataKey="Lower"
              stroke="#22d3ee"
              strokeDasharray="3 3"
              strokeWidth={1}
              dot={false}
              opacity={0.4}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const ForecastChart = React.memo(ForecastChartPresentational);
export default ForecastChart;
