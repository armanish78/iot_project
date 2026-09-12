import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Shield, Activity, Bell, FileSearch, MonitorPlay } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Prediction from './pages/Prediction';
import LiveMonitor from './pages/LiveMonitor';
import { useState, useEffect } from 'react';
import { getHealth } from './api/client';

const Header = () => {
  const [isOnline, setIsOnline] = useState(true);
  
  useEffect(() => {
    getHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));
      
    const interval = setInterval(() => {
      getHealth()
        .then(() => setIsOnline(true))
        .catch(() => setIsOnline(false));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex justify-between items-center mb-8">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Welcome, Administrator</h1>
        <p className="text-[#7BBDE8] font-medium mt-1">Here's your Sentinel network security overview</p>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex flex-col items-end justify-center">
          <span className="text-sm font-bold text-white">{new Date().toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}</span>
          <span className="text-sm text-[#7BBDE8] font-medium font-mono">{new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</span>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'}`}></span>
            <span className="text-[10px] text-[#6EA2B3] uppercase font-bold tracking-wider">{isOnline ? 'System Online' : 'System Offline'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

const Sidebar = () => {
  const navItems = [
    { path: '/', icon: Activity, label: 'Dashboard' },
    { path: '/live', icon: MonitorPlay, label: 'Live Monitor' },
    { path: '/alerts', icon: Bell, label: 'Alerts' },
    { path: '/prediction', icon: FileSearch, label: 'Prediction Test' },
  ];

  return (
    <aside className="w-64 glass-panel m-6 mr-0 flex flex-col relative z-10 flex-shrink-0 h-[calc(100vh-3rem)]">
      <div className="p-8 flex flex-col gap-1 items-center border-b border-[#49769F]/20">
        <div className="flex items-center gap-3">
          <Shield className="text-[#7BBDE8] drop-shadow-[0_0_8px_rgba(123,189,232,0.6)]" size={32} strokeWidth={2} />
          <h1 className="text-2xl font-bold tracking-tight text-white">Sentinel</h1>
        </div>
        <p className="text-[10px] font-medium text-[#6EA2B3] tracking-widest uppercase mt-1">Detect • Analyze • Protect</p>
      </div>
      
      <nav className="flex-1 py-8 px-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink 
            key={item.path}
            to={item.path} 
            className={({isActive}) => `
              flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-300 font-medium
              ${isActive 
                ? 'bg-gradient-to-r from-[#0A4174]/80 to-[#49769F]/30 text-white border border-[#7BBDE8]/30 shadow-[0_0_15px_rgba(123,189,232,0.15)] backdrop-blur-sm relative overflow-hidden' 
                : 'text-[#6EA2B3] hover:bg-[#0A4174]/30 hover:text-white border border-transparent'
              }
            `}
          >
            {({isActive}) => (
              <>
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#7BBDE8] shadow-[0_0_10px_#7BBDE8]"></div>
                )}
                <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} className={isActive ? 'text-[#7BBDE8]' : ''} />
                <span className="tracking-wide text-sm">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-8 mt-auto">
        <div className="relative overflow-hidden rounded-2xl p-5 border border-[#49769F]/20 bg-gradient-to-b from-[#0A4174]/40 to-transparent">
          <div className="absolute -left-4 -top-4 w-24 h-24 bg-[#4E8EA2]/20 rounded-full blur-xl"></div>
          <h3 className="text-white font-bold text-sm relative z-10">Safer</h3>
          <h3 className="text-[#BDD8E9] font-medium text-sm relative z-10">Devices</h3>
          <h3 className="text-white font-bold text-sm relative z-10">Smarter</h3>
          <h3 className="text-[#BDD8E9] font-medium text-sm relative z-10">Tomorrow</h3>
          <div className="mt-4 pt-4 border-t border-[#49769F]/30 relative z-10">
            <svg viewBox="0 0 100 20" className="w-full h-5 stroke-[#7BBDE8] fill-none stroke-2 opacity-70">
              <path d="M0,10 Q10,20 20,10 T40,10 T60,10 T80,10 T100,10" />
            </svg>
          </div>
        </div>
      </div>
    </aside>
  );
};

const App = () => {
  return (
    <Router>
      <div className="flex h-screen overflow-hidden selection:bg-[#4E8EA2]/30">
        <Sidebar />
        
        <main className="flex-1 overflow-auto relative">
          <div className="max-w-[1600px] mx-auto p-6 md:p-8 min-h-full">
            <Header />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/live" element={<LiveMonitor />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/prediction" element={<Prediction />} />
              <Route path="*" element={<div className="glass-card p-12 text-center text-white"><h2 className="text-2xl font-bold mb-2">Coming Soon</h2><p className="text-[#6EA2B3]">This section of Sentinel is currently under development.</p></div>} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
};

export default App;
