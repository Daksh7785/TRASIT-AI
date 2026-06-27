import React, { useState, useEffect } from 'react';
import { 
  Activity, Star, UploadCloud, Compass, BarChart2, ShieldAlert, FileText, 
  Users, Search, Sun, Moon, Sparkles, Terminal, ArrowRight,
  TrendingUp, RefreshCw, X, ChevronRight, CheckCircle2, File
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

// Mock data representing database responses
const INITIAL_CANDIDATES = [
  { id: "TIC_261136679", name: "TOI-125b", mission: "TESS", period: 4.654, depth: 2100, duration: 2.10, confidence: 0.97, status: "Confirmed", ra: 18.3, dec: -45.6 },
  { id: "TIC_307210830", name: "TOI-813b", mission: "TESS", period: 83.891, depth: 870, duration: 11.60, confidence: 0.92, status: "Needs Review", ra: 145.2, dec: 23.4 },
  { id: "TIC_100100827", name: "TOI-132b", mission: "TESS", period: 18.010, depth: 3500, duration: 3.10, confidence: 0.96, status: "Confirmed", ra: 289.4, dec: 12.8 },
  { id: "TIC_149603524", name: "TOI-700d", mission: "TESS", period: 37.424, depth: 1900, duration: 5.00, confidence: 0.94, status: "Confirmed", ra: 98.6, dec: -65.2 },
  { id: "TIC_271893367", name: "TOI-1338b", mission: "TESS", period: 95.200, depth: 340, duration: 7.80, confidence: 0.88, status: "Needs Review", ra: 312.1, dec: -5.4 }
];

const METRICS_TREND = [
  { name: 'Jan', detections: 12, precision: 88 },
  { name: 'Feb', detections: 19, precision: 90 },
  { name: 'Mar', detections: 15, precision: 92 },
  { name: 'Apr', detections: 27, precision: 91 },
  { name: 'May', detections: 34, precision: 93 },
  { name: 'Jun', detections: 42, precision: 94 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<string>("landing");
  const [candidates] = useState(INITIAL_CANDIDATES);
  const [selectedCandidate, setSelectedCandidate] = useState<any>(INITIAL_CANDIDATES[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [aiInput, setAiInput] = useState("");
  const [aiMessages, setAiMessages] = useState<Array<{role: string, text: string}>>([
    { role: 'assistant', text: 'Hello Commander. I can analyze stellar profiles or fetch TESS candidate listings. Try asking: "List transits" or "Is TOI-700d habitable?"' }
  ]);
  
  // File upload state
  const [uploadQueue, setUploadQueue] = useState<Array<{ name: string, size: string, progress: number, status: string }>>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Command palette listener (Ctrl + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleAiMessageSend = () => {
    if (!aiInput.trim()) return;
    const userMsg = aiInput;
    setAiMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setAiInput("");

    setTimeout(() => {
      let respText = "I processed that request. The telemetry parameters are within normal Keplerian limits.";
      if (userMsg.toLowerCase().includes("transit")) {
        respText = "Found 5 candidate transits. Host star TIC_261136679 exhibits a depth of 2100 ppm.";
      } else if (userMsg.toLowerCase().includes("habitable")) {
        respText = "TOI-700d lies within the host star's Optimistic Habitable Zone, receiving approximately 86% of Earth's solar flux.";
      }
      setAiMessages(prev => [...prev, { role: 'assistant', text: respText }]);
    }, 800);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);
    const newFiles = files.map(f => ({
      name: f.name,
      size: `${(f.size / (1024 * 1024)).toFixed(2)} MB`,
      progress: 0,
      status: 'Uploading'
    }));
    setUploadQueue(prev => [...prev, ...newFiles]);

    // Simulate progress
    newFiles.forEach((_, idx) => {
      let prog = 0;
      const interval = setInterval(() => {
        prog += 20;
        setUploadQueue(prev => {
          const clone = [...prev];
          const itemIdx = clone.length - newFiles.length + idx;
          if (clone[itemIdx]) {
            clone[itemIdx].progress = prog;
            if (prog >= 100) {
              clone[itemIdx].status = 'Ready';
              clearInterval(interval);
            }
          }
          return clone;
        });
      }, 300);
    });
  };

  const startBatchAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setUploadQueue([]);
      setActiveTab("dashboard");
    }, 2500);
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-[#0B1026] text-white' : 'bg-gray-50 text-gray-900'} transition-colors duration-300 font-sans relative overflow-x-hidden`}>
      {/* Dynamic Cosmic Background */}
      {isDarkMode && (
        <div className="absolute inset-0 bg-cosmic-gradient opacity-80 pointer-events-none z-0" />
      )}

      {/* Main Layout */}
      <div className="flex relative z-10">
        {/* Navigation Sidebar */}
        {activeTab !== "landing" && (
          <aside className="w-64 border-r border-white/10 min-h-screen flex flex-col justify-between p-4 bg-[#0F1637]/50 backdrop-blur-md sticky top-0 h-screen">
            <div className="space-y-6">
              {/* Logo / Header */}
              <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("landing")}>
                <Activity className="h-8 w-8 text-cyan-400 animate-pulse" />
                <span className="font-bold text-xl bg-gradient-to-r from-cyan-400 via-purple-400 to-indigo-500 bg-clip-text text-transparent">TRANSIT-AI</span>
              </div>

              {/* Navigation Items */}
              <nav className="space-y-1">
                {[
                  { id: "dashboard", label: "Dashboard", icon: BarChart2 },
                  { id: "upload", label: "Upload & Analyze", icon: UploadCloud },
                  { id: "explorer", label: "Candidate Explorer", icon: Compass },
                  { id: "sky-map", label: "Celestial Sky Map", icon: Star },
                  { id: "detail", label: "Transit folded", icon: RefreshCw },
                  { id: "reports", label: "Research Reports", icon: FileText },
                  { id: "community", label: "Community Review", icon: Users },
                ].map(item => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                        activeTab === item.id 
                          ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/30' 
                          : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* User Profile / Info */}
            <div className="pt-4 border-t border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 font-semibold tracking-wider uppercase">System Mode</span>
                <button 
                  onClick={() => setIsDarkMode(!isDarkMode)}
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300"
                >
                  {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-purple-400" />}
                </button>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-white/5 border border-white/5">
                <div className="h-9 w-9 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-[#0B1026]">D</div>
                <div>
                  <div className="text-xs font-semibold text-gray-200">Daksh7785</div>
                  <div className="text-[10px] text-cyan-400">Platform Commander</div>
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Dynamic Pages Area */}
        <main className="flex-1 flex flex-col min-h-screen">
          {/* Top Header Navbar */}
          {activeTab !== "landing" && (
            <header className="h-16 border-b border-white/10 bg-[#0F1637]/35 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-40">
              <div className="flex items-center space-x-4">
                {/* Search / Global Command Palette Launcher */}
                <button 
                  onClick={() => setShowCommandPalette(true)}
                  className="flex items-center space-x-3 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white w-80 text-left text-sm transition-all"
                >
                  <Search className="h-4 w-4" />
                  <span>Search everything...</span>
                  <span className="ml-auto text-xs bg-white/10 px-1.5 py-0.5 rounded font-mono">Ctrl+K</span>
                </button>
              </div>

              {/* Status Header */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-xs bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-3 py-1 rounded-full">
                  <Terminal className="h-3 w-3" />
                  <span>FASTAPI BACKEND: ONLINE</span>
                </div>
                <button 
                  onClick={() => setActiveTab("landing")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Exit Dashboard
                </button>
              </div>
            </header>
          )}

          {/* Main Views Router */}
          <div className="p-8 flex-1">
            <AnimatePresence mode="wait">
              {/* PAGE 1: Landing Page */}
              {activeTab === "landing" && (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }} 
                  exit={{ opacity: 0 }}
                  className="max-w-6xl mx-auto py-16 space-y-24 z-10 relative"
                >
                  {/* Hero Section */}
                  <div className="text-center space-y-6 py-12">
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.5 }}
                      className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm mb-4"
                    >
                      <Sparkles className="h-4 w-4" />
                      <span>Production Release v2.0 Platform</span>
                    </motion.div>
                    
                    <h1 className="text-6xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 via-purple-400 to-indigo-500 bg-clip-text text-transparent">
                      TRANSIT-AI Exoplanet Engine
                    </h1>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                      AI-enabled detection, classification, and parameter estimation of exoplanets from noisy space telescope light curves.
                    </p>
                    
                    <div className="flex items-center justify-center space-x-4 pt-6">
                      <button 
                        onClick={() => setActiveTab("dashboard")}
                        className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-[#0B1026] font-bold rounded-lg shadow-lg shadow-cyan-500/25 flex items-center space-x-2 transition-all duration-300"
                      >
                        <span>Access Telemetry Console</span>
                        <ArrowRight className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={() => setActiveTab("upload")}
                        className="px-8 py-4 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-semibold rounded-lg transition-all"
                      >
                        Upload Light Curves
                      </button>
                    </div>
                  </div>

                  {/* Architecture & Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {[
                      { value: "30k+", label: "Stars Processed" },
                      { value: "400+", label: "Planet Candidates" },
                      { value: "94.2%", label: "Target Precision" },
                      { value: "5-Class", label: "Astrophysical Classifier" },
                    ].map((stat, idx) => (
                      <div key={idx} className="glass-card p-6 text-center border border-white/5 hover:border-cyan-500/20 transition-all duration-300">
                        <div className="text-3xl font-extrabold text-cyan-400">{stat.value}</div>
                        <div className="text-xs text-gray-400 mt-2 uppercase tracking-widest">{stat.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Operational Flow Diagram */}
                  <div className="glass-card p-8 border border-white/5">
                    <h3 className="text-xl font-bold mb-6 text-gray-100 flex items-center space-x-2">
                      <Terminal className="h-5 w-5 text-cyan-400" />
                      <span>Pipeline Operational Flow</span>
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      {[
                        { step: "01", name: "Data Ingest", desc: "TESS/Kepler raw light curve download via MAST" },
                        { step: "02", name: "Outlier Clean", desc: "Iterative MAD filters & TESS flag quality checks" },
                        { step: "03", name: "Period search", desc: "Transit Least Squares (TLS) dip detection" },
                        { step: "04", name: "AI Classify", desc: "Voting ensemble XGBoost/RF & 1D CNN" },
                        { step: "05", name: "MCMC Fit", desc: "Batman Keplerian fitting & HZ estimation" }
                      ].map((item, idx) => (
                        <div key={idx} className="p-4 rounded-lg bg-[#0F1637]/45 border border-white/5 relative">
                          <div className="text-xs text-cyan-400 font-mono font-bold mb-1">{item.step}</div>
                          <div className="text-sm font-bold text-gray-200 mb-2">{item.name}</div>
                          <p className="text-xs text-gray-400 leading-relaxed">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* PAGE 2: Dashboard */}
              {activeTab === "dashboard" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="space-y-8"
                >
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                    {[
                      { label: "Processed Stars", value: "34,281", icon: Star, color: "text-cyan-400" },
                      { label: "Transit Candidates", value: "481", icon: Compass, color: "text-[#00FF88]" },
                      { label: "Vetted False Positives", value: "2,190", icon: ShieldAlert, color: "text-red-400" },
                      { label: "Average Confidence", value: "91.8%", icon: TrendingUp, color: "text-purple-400" },
                      { label: "Active Jobs", value: "0", icon: RefreshCw, color: "text-gray-400" },
                    ].map((item, idx) => {
                      const Icon = item.icon;
                      return (
                        <div key={idx} className="glass-card p-6 border border-white/5">
                          <div className="flex justify-between items-start">
                            <span className="text-xs text-gray-400 font-medium tracking-wide">{item.label}</span>
                            <Icon className={`h-4 w-4 ${item.color}`} />
                          </div>
                          <div className="text-2xl font-bold mt-3 text-gray-100">{item.value}</div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Main Charts area */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Recharts Area Chart */}
                    <div className="glass-card p-6 md:col-span-2 border border-white/5">
                      <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center space-x-2">
                        <TrendingUp className="h-4 w-4 text-cyan-400" />
                        <span>Exoplanet Detection Trends</span>
                      </h3>
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={METRICS_TREND}>
                            <defs>
                              <linearGradient id="colorDetections" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00FF88" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#00FF88" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="#9CA3AF" fontSize={11} />
                            <YAxis stroke="#9CA3AF" fontSize={11} />
                            <Tooltip contentStyle={{ backgroundColor: '#0F1637', border: '1px solid rgba(255,255,255,0.1)' }} />
                            <Area type="monotone" dataKey="detections" stroke="#00FF88" fillOpacity={1} fill="url(#colorDetections)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Detections distribution */}
                    <div className="glass-card p-6 border border-white/5">
                      <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center space-x-2">
                        <Compass className="h-4 w-4 text-purple-400" />
                        <span>Signal Classification</span>
                      </h3>
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={[
                            { name: 'Transit', value: 481, color: '#00FF88' },
                            { name: 'Eclipse', value: 1290, color: '#FFD700' },
                            { name: 'Blend', value: 900, color: '#8B5CF6' },
                            { name: 'Artifact', value: 2040, color: '#EF4444' }
                          ]}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="#9CA3AF" fontSize={10} />
                            <YAxis stroke="#9CA3AF" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0F1637', border: '1px solid rgba(255,255,255,0.1)' }} />
                            <Bar dataKey="value">
                              {[
                                '#00FF88',
                                '#FFD700',
                                '#8B5CF6',
                                '#EF4444'
                              ].map((color, index) => (
                                <Cell key={`cell-${index}`} fill={color} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Recent Candidates List */}
                  <div className="glass-card p-6 border border-white/5">
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center space-x-2">
                      <Activity className="h-4 w-4 text-cyan-400 animate-pulse" />
                      <span>Latest Candidate Telemetry (TESS Sector 1)</span>
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-white/10 text-xs text-gray-400 uppercase tracking-wider">
                            <th className="py-3 px-4">Candidate ID</th>
                            <th className="py-3 px-4">Target Name</th>
                            <th className="py-3 px-4">Period (days)</th>
                            <th className="py-3 px-4">Depth (ppm)</th>
                            <th className="py-3 px-4">Confidence</th>
                            <th className="py-3 px-4">Vetting Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {candidates.map((c, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5 text-sm transition-all">
                              <td className="py-4 px-4 font-mono text-cyan-400">{c.id}</td>
                              <td className="py-4 px-4 font-semibold text-gray-200">{c.name}</td>
                              <td className="py-4 px-4">{c.period.toFixed(3)}</td>
                              <td className="py-4 px-4">{c.depth}</td>
                              <td className="py-4 px-4">
                                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${c.confidence > 0.9 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                                  {(c.confidence * 100).toFixed(0)}%
                                </span>
                              </td>
                              <td className="py-4 px-4">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.status === 'Confirmed' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-purple-500/10 text-purple-400'}`}>
                                  {c.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* PAGE 3: Upload & Analysis */}
              {activeTab === "upload" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="max-w-3xl mx-auto space-y-8"
                >
                  <div className="text-center space-y-2">
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Telemetry File Uploader</h2>
                    <p className="text-gray-400 text-sm">Drag and drop raw TESS/Kepler FITS or CSV files into the pipeline queue.</p>
                  </div>

                  {/* Drag and Drop Zone */}
                  <div className="border-2 border-dashed border-white/10 hover:border-cyan-500/30 rounded-xl p-12 text-center bg-[#0F1637]/45 cursor-pointer relative transition-all duration-300">
                    <input 
                      type="file" 
                      multiple 
                      onChange={handleFileUpload} 
                      className="absolute inset-0 opacity-0 cursor-pointer" 
                    />
                    <UploadCloud className="h-12 w-12 text-cyan-400 mx-auto mb-4 animate-bounce" />
                    <p className="text-sm font-semibold text-gray-200">Drag & Drop files here, or click to browse</p>
                    <p className="text-xs text-gray-500 mt-2">Supports TESS Sector FITS & pipeline-formatted CSV datasets</p>
                  </div>

                  {/* Upload queue */}
                  {uploadQueue.length > 0 && (
                    <div className="glass-card p-6 border border-white/5 space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Processing Queue</h4>
                      <div className="space-y-3">
                        {uploadQueue.map((file, idx) => (
                          <div key={idx} className="p-3 bg-[#0B1026]/60 rounded-lg flex items-center justify-between border border-white/5">
                            <div className="flex items-center space-x-3">
                              <File className="h-4 w-4 text-cyan-400" />
                              <div>
                                <div className="text-xs font-semibold text-gray-200">{file.name}</div>
                                <div className="text-[10px] text-gray-500">{file.size}</div>
                              </div>
                            </div>
                            <div className="w-1/3 flex items-center space-x-3">
                              <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                                <div className="bg-cyan-400 h-full transition-all" style={{ width: `${file.progress}%` }} />
                              </div>
                              <span className="text-xs text-cyan-400 font-bold">{file.progress}%</span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <button
                        onClick={startBatchAnalysis}
                        disabled={isAnalyzing}
                        className="w-full py-4 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-[#0B1026] font-bold rounded-lg transition-all duration-300 flex items-center justify-center space-x-2"
                      >
                        {isAnalyzing ? (
                          <>
                            <RefreshCw className="h-4 w-4 animate-spin" />
                            <span>Computing Light Curve Inversion...</span>
                          </>
                        ) : (
                          <span>Start Pipeline Analysis</span>
                        )}
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {/* PAGE 6: Candidate Explorer */}
              {activeTab === "explorer" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Exoplanet Candidate Registry</h2>
                    <input 
                      type="text"
                      placeholder="Search ID, Period, Status..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400 w-80"
                    />
                  </div>

                  <div className="glass-card border border-white/5 overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-white/10 text-xs text-gray-400 uppercase tracking-wider">
                          <th className="py-3 px-4">TIC ID</th>
                          <th className="py-3 px-4">Planet Name</th>
                          <th className="py-3 px-4">Mission</th>
                          <th className="py-3 px-4">Period (days)</th>
                          <th className="py-3 px-4">Depth (ppm)</th>
                          <th className="py-3 px-4">Confidence</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {candidates.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.id.toLowerCase().includes(searchQuery.toLowerCase())).map((c, idx) => (
                          <tr key={idx} className="border-b border-white/5 hover:bg-white/5 text-sm transition-all">
                            <td className="py-4 px-4 font-mono text-cyan-400">{c.id}</td>
                            <td className="py-4 px-4 font-semibold text-gray-200">{c.name}</td>
                            <td className="py-4 px-4">{c.mission}</td>
                            <td className="py-4 px-4">{c.period.toFixed(3)}</td>
                            <td className="py-4 px-4">{c.depth}</td>
                            <td className="py-4 px-4">{(c.confidence * 100).toFixed(0)}%</td>
                            <td className="py-4 px-4">
                              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${c.status === 'Confirmed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                                {c.status}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-right">
                              <button 
                                onClick={() => {
                                  setSelectedCandidate(c);
                                  setActiveTab("detail");
                                }}
                                className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-cyan-300 rounded transition-all"
                              >
                                View telemetry
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}

              {/* PAGE 7: Interactive Sky Map */}
              {activeTab === "sky-map" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Celestial Coordinate Sky Map</h2>
                  
                  {/* Sky Map Visualization placeholder with coordinates */}
                  <div className="glass-card p-8 border border-white/5 h-[500px] flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute inset-0 bg-[#0B1026]/90 flex items-center justify-center">
                      {/* Grid representation */}
                      <div className="absolute inset-0 opacity-10 flex items-center justify-center">
                        <div className="w-full h-full border border-dashed border-white rounded-full scale-90" />
                        <div className="w-full h-full border border-dashed border-white rounded-full scale-75 absolute" />
                        <div className="w-full h-full border border-dashed border-white rounded-full scale-50 absolute" />
                        <div className="w-[1px] h-full bg-white absolute" />
                        <div className="h-[1px] w-full bg-white absolute" />
                      </div>
                      
                      {/* Star Candidate Markers */}
                      {candidates.map((c, idx) => (
                        <div
                          key={idx}
                          style={{
                            position: 'absolute',
                            left: `${45 + (c.ra - 100) / 5}%`,
                            top: `${45 + (c.dec + 20) / 2}%`
                          }}
                          className="h-3 w-3 bg-[#00FF88] rounded-full animate-ping cursor-pointer relative"
                          onClick={() => setSelectedCandidate(c)}
                        >
                          <span className="absolute left-4 top-[-6px] text-xs font-mono bg-[#0F1637] border border-white/10 px-2 py-0.5 rounded text-white whitespace-nowrap shadow-lg">
                            {c.name} (RA:{c.ra})
                          </span>
                        </div>
                      ))}
                    </div>
                    
                    <div className="relative z-10 flex justify-between items-end w-full">
                      <div className="space-y-2">
                        <h4 className="text-sm font-bold text-gray-200">Selected Star Profile</h4>
                        {selectedCandidate ? (
                          <div className="text-xs text-gray-400 space-y-1">
                            <div>Name: <span className="text-cyan-400">{selectedCandidate.name}</span></div>
                            <div>RA: {selectedCandidate.ra}° | Dec: {selectedCandidate.dec}°</div>
                            <div>Period: {selectedCandidate.period} days</div>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-500">Click a marker to view telemetry</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 font-mono">TESS GALACTIC COORDINATE SYSTEM v2</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* PAGE 5: Light Curve / Candidate Detail Page */}
              {activeTab === "detail" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="space-y-8"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-3xl font-extrabold text-gray-100 flex items-center space-x-3">
                        <span>{selectedCandidate?.name || "TOI-125b"}</span>
                        <span className="text-sm px-2.5 py-1 rounded bg-[#00FF88]/10 border border-[#00FF88]/30 text-[#00FF88]">TRANSIT CANDIDATE</span>
                      </h2>
                      <p className="text-xs text-gray-400 font-mono mt-1">Host Star: {selectedCandidate?.id || "TIC_261136679"}</p>
                    </div>
                    <button 
                      onClick={() => setActiveTab("explorer")}
                      className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-xs text-gray-400 hover:text-white"
                    >
                      Back to Explorer
                    </button>
                  </div>

                  {/* Primary Telemetry Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left: Metadata */}
                    <div className="glass-card p-6 border border-white/5 space-y-6">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Physical Parameters</h3>
                      
                      <div className="space-y-4">
                        {[
                          { label: "Orbital Period", value: `${selectedCandidate?.period.toFixed(4) || "4.6546"} days` },
                          { label: "Transit Depth", value: `${selectedCandidate?.depth || "2100"} ppm` },
                          { label: "Transit Duration", value: `${selectedCandidate?.duration.toFixed(2) || "2.10"} hours` },
                          { label: "Classification", value: "TRANSIT" },
                          { label: "Confidence", value: `${((selectedCandidate?.confidence || 0.97) * 100).toFixed(0)}%` },
                        ].map((param, idx) => (
                          <div key={idx} className="flex justify-between border-b border-white/5 pb-2 text-sm">
                            <span className="text-gray-400">{param.label}</span>
                            <span className="font-semibold text-gray-200">{param.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Center: Fake Phase Fold Curve representation */}
                    <div className="glass-card p-6 md:col-span-2 border border-white/5 flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-6">Phase Folded Light Curve</h3>
                        {/* Simulation of a folded dip */}
                        <div className="h-48 bg-[#0B1026]/90 border border-white/5 rounded-lg flex items-center justify-center relative">
                          <div className="absolute inset-0 opacity-10 flex flex-col justify-between py-4">
                            <div className="h-[1px] bg-white w-full" />
                            <div className="h-[1px] bg-white w-full" />
                            <div className="h-[1px] bg-white w-full" />
                          </div>
                          
                          {/* Symmetrical transit dip representation */}
                          <svg className="w-full h-full text-cyan-400" viewBox="0 0 500 200">
                            <path 
                              d="M 0 50 L 200 50 L 220 150 L 280 150 L 300 50 L 500 50" 
                              fill="none" 
                              stroke="currentColor" 
                              strokeWidth="3" 
                            />
                            {/* Points scatter representation */}
                            <circle cx="50" cy="52" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="100" cy="48" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="150" cy="51" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="210" cy="95" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="230" cy="148" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="250" cy="152" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="270" cy="149" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="290" cy="100" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="350" cy="49" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="400" cy="53" r="3" fill="#00FF88" className="opacity-60" />
                            <circle cx="450" cy="50" r="3" fill="#00FF88" className="opacity-60" />
                          </svg>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center text-xs text-gray-500 pt-4 font-mono">
                        <span>Phase (-0.5 to 0.5)</span>
                        <span>Normalized Relative Flux</span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Explainability & Review section */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Left: Explainability */}
                    <div className="glass-card p-6 md:col-span-2 border border-white/5 space-y-4">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Explainable AI (XAI) Insight</h3>
                      <blockquote className="p-4 bg-[#0B1026]/60 border-l-4 border-cyan-400 rounded text-sm text-gray-300 leading-relaxed font-mono">
                        "Ensemble classifier confidence: 97% because symmetric U-shaped geometry, absence of secondary eclipses at phase 0.5, and high SNR (18.4σ) strongly rule out Eclipsing Binary or Stellar Blend variants."
                      </blockquote>
                    </div>

                    {/* Right: Community review */}
                    <div className="glass-card p-6 border border-white/5 space-y-4">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">Vetting Consensus</h3>
                      <div className="flex justify-between items-center bg-[#0B1026]/40 p-3 rounded-lg border border-white/5">
                        <span className="text-xs text-gray-400">Current Verdict</span>
                        <span className="text-sm font-bold text-[#00FF88] flex items-center space-x-1">
                          <CheckCircle2 className="h-4 w-4" />
                          <span>CONFIRMED</span>
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 pt-2">
                        <button className="flex-1 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-xs font-semibold">Verify Planet</button>
                        <button className="flex-1 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-xs font-semibold">Flag EB</button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* PAGE 11: Reports Page */}
              {activeTab === "reports" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="max-w-3xl mx-auto space-y-6"
                >
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Telemetry & Research Reports</h2>
                  <p className="text-gray-400 text-sm">Download processed exoplanetary catalog results in multiple telemetry formats.</p>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                      { type: "PDF Report", desc: "Scientific 3-page vetting report including MCMC model parameters & explainability charts.", format: "PDF", size: "48 KB" },
                      { type: "Pipeline Results", desc: "Raw tabular dump containing periods, depths, and classification labels.", format: "CSV", size: "12 KB" },
                      { type: "Telemetry Payload", desc: "Raw JSON structure representing candidate coordinate features.", format: "JSON", size: "8 KB" }
                    ].map((rep, idx) => (
                      <div key={idx} className="glass-card p-6 border border-white/5 flex flex-col justify-between h-48 hover:border-cyan-500/20 transition-all">
                        <div>
                          <div className="flex justify-between items-start mb-3">
                            <span className="text-sm font-bold text-gray-200">{rep.type}</span>
                            <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-gray-400">{rep.format}</span>
                          </div>
                          <p className="text-xs text-gray-400 leading-relaxed">{rep.desc}</p>
                        </div>
                        <div className="flex items-center justify-between text-xs text-cyan-400 pt-4">
                          <span>{rep.size}</span>
                          <button className="hover:underline font-semibold">Download file</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* PAGE 12: Community Review Portal */}
              {activeTab === "community" && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0 }}
                  className="max-w-4xl mx-auto space-y-6"
                >
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Collaborative Vetting Consensus</h2>
                  <p className="text-gray-400 text-sm">Coordinate votes and expert telemetry peer-review reviews on candidate orbits.</p>

                  <div className="space-y-4">
                    {candidates.map((c, idx) => (
                      <div key={idx} className="glass-card p-5 border border-white/5 flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="text-sm font-bold text-gray-200">{c.name} ({c.id})</div>
                          <div className="text-xs text-gray-400">Period: {c.period.toFixed(3)} days | Depth: {c.depth} ppm</div>
                        </div>
                        <div className="flex items-center space-x-6">
                          <div className="flex flex-col items-end">
                            <span className="text-[10px] text-gray-500 uppercase tracking-widest">Consensus</span>
                            <span className="text-xs font-semibold text-cyan-400">{c.status}</span>
                          </div>
                          <button className="px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-semibold rounded-lg transition-all border border-cyan-500/20">Vote candidate</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Floating AI Assistant Widget */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsAiOpen(prev => !prev)}
          className="h-14 w-14 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 shadow-xl shadow-cyan-500/20 flex items-center justify-center text-white transition-all duration-300 relative"
        >
          {isAiOpen ? <X className="h-6 w-6" /> : <Sparkles className="h-6 w-6" />}
        </button>

        <AnimatePresence>
          {isAiOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="absolute bottom-16 right-0 w-96 h-[400px] glass-card border border-white/10 flex flex-col justify-between overflow-hidden shadow-2xl"
            >
              <div className="p-4 border-b border-white/10 bg-[#0F1637]/75 backdrop-blur-md flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-200">AstroLens AI Copilot</span>
                </div>
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>

              {/* Chat messages */}
              <div className="p-4 flex-1 overflow-y-auto space-y-3 font-mono text-xs">
                {aiMessages.map((m, idx) => (
                  <div key={idx} className={`p-2.5 rounded-lg max-w-[85%] ${m.role === 'user' ? 'bg-cyan-500/10 text-cyan-300 ml-auto' : 'bg-white/5 text-gray-300'}`}>
                    {m.text}
                  </div>
                ))}
              </div>

              {/* Chat input */}
              <div className="p-3 border-t border-white/10 flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Ask telemetry copilot..."
                  value={aiInput}
                  onChange={(e) => setAiInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAiMessageSend()}
                  className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-xs focus:outline-none focus:border-cyan-400 text-white"
                />
                <button
                  onClick={handleAiMessageSend}
                  className="px-3 py-2 bg-cyan-500 hover:bg-cyan-400 text-[#0B1026] font-bold text-xs rounded-lg transition-all"
                >
                  Send
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Global Command Palette Dialog Modal (Ctrl + K) */}
      <AnimatePresence>
        {showCommandPalette && (
          <div className="fixed inset-0 z-50 bg-[#0B1026]/75 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg glass-card border border-white/10 overflow-hidden shadow-2xl"
            >
              <div className="p-4 border-b border-white/10 flex items-center space-x-3">
                <Search className="h-5 w-5 text-cyan-400" />
                <input 
                  type="text"
                  placeholder="Search pages or action commands..."
                  className="bg-transparent text-sm text-white focus:outline-none w-full"
                />
                <button onClick={() => setShowCommandPalette(false)}>
                  <X className="h-4 w-4 text-gray-400 hover:text-white" />
                </button>
              </div>

              {/* Commands list */}
              <div className="p-2 space-y-1">
                {[
                  { label: "Go to Dashboard", cmd: "dashboard" },
                  { label: "Verify TESS Target Sector", cmd: "explorer" },
                  { label: "Upload CSV/FITS telemetry", cmd: "upload" },
                  { label: "View Reports Catalogue", cmd: "reports" }
                ].map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setActiveTab(item.cmd);
                      setShowCommandPalette(false);
                    }}
                    className="w-full text-left px-4 py-3 rounded-lg hover:bg-white/5 text-xs text-gray-300 flex items-center justify-between"
                  >
                    <span>{item.label}</span>
                    <ChevronRight className="h-3 w-3 text-cyan-400" />
                  </button>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
