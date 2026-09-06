import { useEffect, useState } from 'react';
import { getAlerts } from '../api/client';
import { AlertOctagon, CheckCircle2, ShieldAlert, AlertTriangle, Info } from 'lucide-react';

const Alerts = () => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAlerts()
      .then(res => setAlerts(res.data.alerts || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getSeverityIcon = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <ShieldAlert size={16} className="text-red-500" />;
      case 'high': return <AlertOctagon size={16} className="text-orange-500" />;
      case 'medium': return <AlertTriangle size={16} className="text-amber-500" />;
      default: return <Info size={16} className="text-blue-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const s = severity?.toLowerCase();
    if (s === 'critical') return 'bg-red-500/10 text-red-400 border-red-500/20';
    if (s === 'high') return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
    if (s === 'medium') return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Security Alerts</h2>
          <p className="text-slate-400 mt-1">Active threats requiring investigation.</p>
        </div>
        <div className="bg-red-500/10 text-red-400 px-4 py-2 rounded-lg font-bold border border-red-500/20 flex items-center gap-2 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
          <span className="relative flex h-2 w-2 mr-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </span>
          {alerts.length} ACTIVE
        </div>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center text-indigo-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
          <span className="font-semibold tracking-wide">Loading alerts...</span>
        </div>
      ) : (
        <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-sm overflow-hidden">
          {alerts.length === 0 ? (
            <div className="p-16 text-center flex flex-col items-center justify-center">
              <div className="bg-emerald-500/10 p-4 rounded-full mb-4">
                <CheckCircle2 size={48} className="text-emerald-500" />
              </div>
              <h3 className="text-xl text-white font-bold tracking-wide">No Active Alerts</h3>
              <p className="text-slate-400 mt-2">Your IoT network is currently secure. No anomalies detected.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left whitespace-nowrap">
                <thead className="bg-[#0d131f] text-slate-400 text-xs uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-4">Time</th>
                    <th className="px-6 py-4">Severity</th>
                    <th className="px-6 py-4">Threat Type</th>
                    <th className="px-6 py-4">Message / Details</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {alerts.map((alert: any) => {
                    const date = new Date(alert.timestamp);
                    const timeString = `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour12: false })}`;
                    
                    return (
                      <tr key={alert.id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="px-6 py-4 text-sm text-slate-400">{timeString}</td>
                        <td className="px-6 py-4">
                          <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-bold border ${getSeverityBadge(alert.severity)}`}>
                            {getSeverityIcon(alert.severity)}
                            <span className="uppercase">{alert.severity || 'Unknown'}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-sm font-semibold text-slate-200 capitalize tracking-wide">
                            {alert.alert_type?.replace('_', ' ') || 'Threat Detected'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm font-mono text-slate-400 truncate max-w-md group-hover:text-slate-300 transition-colors">
                            {alert.message || 'No additional details provided.'}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider border ${
                            alert.status === 'new' 
                              ? 'bg-red-500/10 text-red-400 border-red-500/20' 
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}>
                            {alert.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Alerts;
