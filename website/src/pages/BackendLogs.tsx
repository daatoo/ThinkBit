import { useEffect, useState } from "react";
import Header from "../components/Header";
import Footer from "../components/Footer";

const BackendLogs = () => {
  const [logs, setLogs] = useState<string>("Loading logs...");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchLogs = async () => {
    try {
      // Use relative URL so it works via proxy in dev and same-origin in prod
      const response = await fetch("/debug/logs");
      if (!response.ok) {
        throw new Error("Failed to fetch logs");
      }
      const text = await response.text();
      setLogs(text || "No logs available.");
      setLastUpdated(new Date());
    } catch (error) {
      console.error(error);
      setLogs("Error fetching logs. Ensure backend is running.");
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col font-mono">
      <Header />

      <main className="flex-grow pt-24 pb-12 px-4 md:px-8 max-w-7xl mx-auto w-full">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl md:text-4xl font-bold gradient-text glitch-text" data-text="System Logs">
            System Logs
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground hidden md:inline">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
            <button
              onClick={fetchLogs}
              className="px-4 py-2 border border-primary/50 hover:bg-primary/10 text-primary rounded transition-colors text-sm uppercase tracking-wider"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="relative group">
          {/* Neon Glow Border Effect */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-secondary rounded-lg opacity-75 group-hover:opacity-100 blur transition duration-1000 group-hover:duration-200"></div>

          <div className="relative bg-[#1a1025] rounded-lg p-6 h-[70vh] overflow-auto shadow-2xl border border-border/50">
            <pre className="font-mono text-sm md:text-base whitespace-pre-wrap break-all" style={{ color: '#00ff9f', textShadow: '0 0 5px rgba(0, 255, 159, 0.5)' }}>
              {logs.split('\n').map((line, i) => {
                let className = "";
                let style = {};
                if (line.includes("INFO")) {
                  style = { color: '#00ff9f' }; // Neon Green
                } else if (line.includes("WARNING")) {
                  style = { color: '#ffff00' }; // Yellow
                } else if (line.includes("ERROR") || line.includes("Exception") || line.includes("Traceback")) {
                  style = { color: '#ff0055', textShadow: '0 0 8px rgba(255, 0, 85, 0.8)' }; // Neon Red
                } else {
                  style = { color: '#d4d4d4' }; // Default gray
                }
                return (
                  <div key={i} style={style}>
                    {line}
                  </div>
                );
              })}
            </pre>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default BackendLogs;
