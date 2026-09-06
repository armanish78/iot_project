import { useEffect, useState } from 'react';
import { getHealth, getDashboardStats, getDashboardActivity } from '../api/client';
import { ServerCrash, Server, ShieldAlert, ShieldCheck, Activity } from 'lucide-react';

const Dashboard = () => {
  const [health, setHealth] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, statsRes, activityRes] = await Promise.all([
          getHealth().catch(() => ({ data: { status: 'offline' } })),
          getDashboardStats().catch(() => ({ data: null })),
          getDashboardActivity(50).catch(() => ({ data: { activity: [] } }))
        ]);
        
        setHealth(healthRes.data);
        if (statsRes.data?.stats) setStats(statsRes.data.stats);
        if (activityRes.data?.activity) setActivity(activityRes.data.activity);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-indigo-400">
        <Activity className="animate-spin mr-3" size={24} />
        <span className="font-semibold tracking-wide">Loading dashboard data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold text-white tracking-tight">SOC Dashboard</h2>
        <p className="text-slate-400 mt-1">Real-time network security overview.</p>
      </div>
      
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${health?.status === 'healthy' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {health?.status === 'healthy' ? <Server size={22} /> : <ServerCrash size={22} />}
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">System Status</p>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                <p className="text-xl font-bold text-white capitalize">{health?.status || 'Unknown'}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400">
              <ShieldCheck size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Scans</p>
              <p className="text-2xl font-bold text-white font-mono">{stats?.total_connections?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-red-500/10 text-red-400">
              <ShieldAlert size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Threats Detected</p>
              <p className="text-2xl font-bold text-white font-mono">{stats?.threats_detected?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-amber-500"></div>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-amber-500/10 text-amber-400">
              <Activity size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Threat Rate</p>
              <p className="text-2xl font-bold text-white font-mono">{stats ? (stats.threat_rate * 100).toFixed(1) : 0}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="px-6 py-5 border-b border-slate-800 flex justify-between items-center bg-[#0d131f]">
          <h3 className="font-bold text-white tracking-wide">Recent Network Activity</h3>
          <span className="text-xs font-medium bg-slate-800 text-slate-300 px-3 py-1 rounded-full">Last 50 events</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left whitespace-nowrap">
            <thead className="bg-[#111827] text-slate-400 text-xs uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Time</th>
                <th className="px-6 py-4">Source IP</th>
                <th className="px-6 py-4">Destination IP</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {activity.map((item, idx) => {
                const date = new Date(item.timestamp);
                const timeString = `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour12: false })}`;
                
                return (
                  <tr key={item.id || idx} className="hover:bg-slate-800/30 transition-colors group">
                    <td className="px-6 py-4 text-sm text-slate-400">{timeString}</td>
                    <td className="px-6 py-4 font-mono text-sm text-slate-300 group-hover:text-indigo-300 transition-colors">{item.source_ip}</td>
                    <td className="px-6 py-4 font-mono text-sm text-slate-300 group-hover:text-indigo-300 transition-colors">{item.dest_ip}</td>
                    <td className="px-6 py-4">
                      {item.threat ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-2 animate-pulse"></span>
                          THREAT
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2"></span>
                          SAFE
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {activity.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                    No recent network activity available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
