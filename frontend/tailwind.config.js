// Tailwind config. Owner: Person D. AQI color scale used across map + panels.
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aqi: {
          good: "#22c55e",     // green
          moderate: "#eab308", // yellow
          poor: "#ef4444",     // red
          severe: "#7f1d1d",   // dark-red
        },
      },
    },
  },
  plugins: [],
};
