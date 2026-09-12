import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardStats, getDashboardActivity, getAlerts, getLiveStatus } from '../api/client';
import { ShieldAlert, Server, MonitorPlay, CheckCircle, Bell } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [liveStatus, setLiveStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, activityRes, alertsRes, liveRes] = await Promise.all([
          getDashboardStats().catch(() => ({ data: { total_predictions: 0, threat_count: 0, benign_count: 0 } })),
          getDashboardActivity(50).catch(() => ({ data: [] })),
          getAlerts().catch(() => ({ data: { alerts: [] } })),
          getLiveStatus().catch(() => ({ data: { running: false } }))
        ]);

        setStats(statsRes.data);
        setActivity(activityRes.data?.activity || []);
        setAlerts(alertsRes.data?.alerts || []);
        setLiveStatus(liveRes.data);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-8 text-[#BDD8E9] animate-pulse font-medium">Loading Sentinel Dashboard...</div>;
  }

  // Format activity data for charts (bucket by minute)
  const buildChartData = (events: any[]) => {
    if (!events || events.length === 0) return [];
    const buckets: Record<string, { total: number, threats: number }> = {};
    
    events.forEach(event => {
      if (!event.timestamp) return;
      const date = new Date(event.timestamp);
      date.setSeconds(0, 0); // group by minute
      const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      if (!buckets[timeStr]) buckets[timeStr] = { total: 0, threats: 0 };
      buckets[timeStr].total += 1;
      if (event.threat) buckets[timeStr].threats += 1;
    });

    return Object.keys(buckets).sort().map(time => ({
      time,
      total: buckets[time].total,
      threats: buckets[time].threats
    }));
  };
  
  const chartData = buildChartData(activity);

  // Threat types pie chart data
  const threatTypesMap: Record<string, number> = {};
  alerts.forEach(a => {
    const t = a.threat_type || 'Unknown';
    threatTypesMap[t] = (threatTypesMap[t] || 0) + 1;
  });
  const pieData = Object.keys(threatTypesMap).map(key => ({
    name: key,
    value: threatTypesMap[key]
  }));
  const PIE_COLORS = ['#7BBDE8', '#4E8EA2', '#0A4174', '#BDD8E9', '#6EA2B3'];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* SUMMARY CARDS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 flex items-center gap-5 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-24 h-24 bg-[#0A4174]/50 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="w-14 h-14 rounded-full bg-[#001D39]/80 border border-[#49769F]/50 flex items-center justify-center flex-shrink-0 relative z-10">
            <Server className="text-[#7BBDE8]" size={24} />
          </div>
          <div className="relative z-10">
            <p className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Total Scans</p>
            <h3 className="text-3xl font-black text-white mt-1 leading-none">{stats?.stats?.total_connections?.toLocaleString() || 0}</h3>
            <p className="text-[11px] font-medium text-[#4E8EA2] mt-1.5">Historical predictions</p>
          </div>
        </div>

        <div className="glass-card p-6 flex items-center gap-5 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-24 h-24 bg-red-500/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="w-14 h-14 rounded-full bg-[#001D39]/80 border border-red-500/30 flex items-center justify-center flex-shrink-0 relative z-10">
            <ShieldAlert className="text-red-400" size={24} />
          </div>
          <div className="relative z-10">
            <p className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Threats Detected</p>
            <div className="flex items-end gap-2 mt-1">
              <h3 className="text-3xl font-black text-white leading-none">{stats?.stats?.threats_detected?.toLocaleString() || 0}</h3>
              {stats?.stats?.threats_detected > 0 && <span className="text-xs font-bold text-red-400 mb-1">Active</span>}
            </div>
            <p className="text-[11px] font-medium text-[#4E8EA2] mt-1.5">Across all monitored traffic</p>
          </div>
        </div>

        <div className="glass-card p-6 flex items-center gap-5 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="w-14 h-14 rounded-full bg-[#001D39]/80 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 relative z-10">
            <MonitorPlay className={liveStatus?.running ? "text-emerald-400" : "text-slate-400"} size={24} />
          </div>
          <div className="relative z-10">
            <p className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Live Status</p>
            <h3 className={`text-2xl font-black mt-1 leading-none ${liveStatus?.running ? 'text-emerald-400' : 'text-slate-300'}`}>
              {liveStatus?.running ? 'Monitoring' : 'Stopped'}
            </h3>
            <p className="text-[11px] font-medium text-[#4E8EA2] mt-1.5">{liveStatus?.running ? 'Capturing packets...' : 'System idle'}</p>
          </div>
        </div>

        <div className="glass-card p-6 flex items-center gap-5 relative overflow-hidden">
          <div className="absolute right-0 top-0 w-24 h-24 bg-[#7BBDE8]/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="w-14 h-14 rounded-full bg-[#001D39]/80 border border-[#49769F]/50 flex items-center justify-center flex-shrink-0 relative z-10">
            <CheckCircle className="text-[#BDD8E9]" size={24} />
          </div>
          <div className="relative z-10">
            <p className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">System Health</p>
            <h3 className="text-2xl font-black text-white mt-1 leading-none">Operational</h3>
            <p className="text-[11px] font-medium text-[#4E8EA2] mt-1.5">All services responding</p>
          </div>
        </div>
      </div>

      {/* CHARTS ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                Network Traffic (Recent)
              </h2>
              <p className="text-xs font-medium text-[#6EA2B3] mt-1">Real-time prediction volume</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-bold">
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-[#7BBDE8]"></div> Total Traffic</span>
              <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-red-400"></div> Threats</span>
            </div>
          </div>
          
          <div className="h-64 w-full">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7BBDE8" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#7BBDE8" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#49769F" opacity={0.2} vertical={false} />
                  <XAxis dataKey="time" stroke="#6EA2B3" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#6EA2B3" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(0, 29, 57, 0.9)', borderColor: '#49769F', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    itemStyle={{ color: '#BDD8E9' }}
                  />
                  <Area type="monotone" dataKey="total" stroke="#7BBDE8" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" />
                  <Area type="monotone" dataKey="threats" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorThreats)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex items-center justify-center border border-dashed border-[#49769F]/30 rounded-xl">
                <span className="text-[#6EA2B3] text-sm">No recent activity data available</span>
              </div>
            )}
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Threat Types</h2>
              <p className="text-xs font-medium text-[#6EA2B3] mt-1">Distribution of active alerts</p>
            </div>
          </div>
          
          <div className="h-64 w-full flex items-center justify-center relative">
            {pieData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {pieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'rgba(0, 29, 57, 0.9)', borderColor: '#49769F', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                      itemStyle={{ color: '#BDD8E9' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-3xl font-black text-white">{alerts.length}</span>
                  <span className="text-[10px] font-bold text-[#6EA2B3] uppercase tracking-wider">Alerts</span>
                </div>
              </>
            ) : (
               <div className="w-full h-full flex items-center justify-center border border-dashed border-[#49769F]/30 rounded-xl">
                 <span className="text-[#6EA2B3] text-sm">No threat data available</span>
               </div>
            )}
          </div>
        </div>
      </div>

      {/* RECENT ALERTS */}
      <div className="glass-card p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Bell size={18} className="text-[#7BBDE8]" />
              Recent Alerts
            </h2>
            <p className="text-xs font-medium text-[#6EA2B3] mt-1">Latest detected threats from your network</p>
          </div>
          <Link to="/alerts" className="glass-button px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-white hover:text-white">See all</Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#49769F]/30">
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Time</th>
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Source IP</th>
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Destination IP</th>
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Threat Type</th>
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider">Confidence</th>
                <th className="pb-3 text-xs font-bold text-[#6EA2B3] uppercase tracking-wider text-right">Status</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {alerts.length > 0 ? (
                alerts.slice(0, 6).map((alert, idx) => (
                  <tr key={idx} className="border-b border-[#49769F]/10 hover:bg-[#0A4174]/20 transition-colors">
                    <td className="py-4 text-[#BDD8E9] whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="py-4 font-mono text-[#7BBDE8]">{alert.source_ip}</td>
                    <td className="py-4 font-mono text-slate-400">{alert.dest_ip}</td>
                    <td className="py-4 text-white font-medium">{alert.threat_type}</td>
                    <td className="py-4 text-[#BDD8E9]">{Math.round((alert.confidence || 0) * 100)}%</td>
                    <td className="py-4 text-right">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                        alert.severity === 'high' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                        alert.severity === 'medium' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                        'bg-blue-500/20 text-blue-400 border-blue-500/30'
                      }`}>
                        {alert.severity || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#6EA2B3]">No recent alerts found. System is secure.</td>
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
