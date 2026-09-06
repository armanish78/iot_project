import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Shield, Activity, Bell, FileSearch } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Prediction from './pages/Prediction';

const App = () => {
  return (
    <Router>
      <div className="flex h-screen bg-[#0a0f18] text-slate-300 font-sans selection:bg-indigo-500/30">
        {/* Sidebar */}
        <aside className="w-64 bg-[#111827] border-r border-slate-800 flex flex-col relative z-10 shadow-xl">
          <div className="p-6 flex flex-col gap-1 border-b border-slate-800/50">
            <div className="flex items-center gap-3">
              <Shield className="text-emerald-500" size={28} strokeWidth={2.5} />
              <h1 className="text-xl font-bold tracking-wide text-white">IoT SECURE</h1>
            </div>
            <p className="text-xs font-medium text-slate-500 tracking-wider uppercase ml-10">Threat Detection</p>
          </div>
          
          <nav className="flex-1 py-6 px-4 space-y-1 overflow-y-auto">
            <NavLink 
              to="/" 
              className={({isActive}) => `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium ${isActive ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.05)]' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
            >
              <Activity size={20} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink 
              to="/alerts" 
              className={({isActive}) => `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium ${isActive ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.05)]' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
            >
              <Bell size={20} />
              <span>Alerts</span>
            </NavLink>
            <NavLink 
              to="/prediction" 
              className={({isActive}) => `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium ${isActive ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.05)]' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
            >
              <FileSearch size={20} />
              <span>Prediction Test</span>
            </NavLink>
          </nav>

          <div className="p-4 border-t border-slate-800 bg-[#0d131f]">
            <div className="flex items-center gap-3 px-2">
              <div className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </div>
              <span className="text-xs font-semibold text-emerald-500 tracking-wider">API ONLINE</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-[#0a0f18] text-slate-300 relative">
          <div className="max-w-7xl mx-auto p-6 md:p-8 lg:p-10">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/prediction" element={<Prediction />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
};

export default App;
