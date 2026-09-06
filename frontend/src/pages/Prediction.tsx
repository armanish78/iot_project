import { useState } from 'react';
import { runPrediction } from '../api/client';
import { Play, ShieldAlert, ShieldCheck, Activity, Cpu, Network, Zap } from 'lucide-react';
import samplePacket from '../sample_packet.json';

const Prediction = () => {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTestPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runPrediction(samplePacket);
      setResult(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to run prediction');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Find max value to render proportional bars
  const maxFeatureValue = result?.top_features 
    ? Math.max(...result.top_features.map((f: any) => Math.abs(f.value)))
    : 1;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-5xl mx-auto">
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-3xl font-bold text-white tracking-tight">Threat Detection Engine</h2>
        <p className="text-slate-400 mt-1">Run active packet analysis using the Hybrid ML pipeline.</p>
      </div>
      
      <div className="bg-[#111827] rounded-xl p-8 border border-slate-800 shadow-sm relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <h3 className="font-bold text-white text-lg flex items-center gap-2">
              <Network size={20} className="text-indigo-400" />
              Analyze Network Packet
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Ready to test the hybrid ML engine with a real 167-feature network packet captured from the IoT dataset. 
              This sample bypasses standard threshold rules to test the behavioral analysis capabilities.
            </p>
          </div>
          
          <button 
            onClick={handleTestPrediction}
            disabled={loading}
            className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_25px_rgba(79,70,229,0.5)] border border-indigo-500/50 min-w-[220px]"
          >
            {loading ? (
              <Activity className="animate-spin" size={20} />
            ) : (
              <Play size={20} fill="currentColor" />
            )}
            {loading ? 'Analyzing Packet...' : 'Run Prediction'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-xl flex items-start gap-4">
          <ShieldAlert className="mt-0.5 shrink-0" size={20} />
          <div>
            <h4 className="font-bold mb-1">Analysis Failed</h4>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="flex items-center gap-3">
            <Cpu size={24} className="text-slate-400" />
            <h3 className="text-xl font-bold text-white tracking-wide">Analysis Results</h3>
          </div>
          
          <div className={`p-8 rounded-xl border shadow-lg relative overflow-hidden ${
            result.threat ? 'bg-[#15121b] border-red-500/30' : 'bg-[#0f1715] border-emerald-500/30'
          }`}>
            {/* Background glow */}
            <div className={`absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl opacity-10 pointer-events-none ${
              result.threat ? 'bg-red-500' : 'bg-emerald-500'
            }`}></div>

            <div className="flex flex-col lg:flex-row gap-10 relative z-10">
              
              {/* Primary Status Column */}
              <div className="lg:w-1/3 flex flex-col items-center justify-center text-center space-y-4 border-b lg:border-b-0 lg:border-r border-slate-800/50 pb-8 lg:pb-0 lg:pr-8">
                <div className={`p-5 rounded-full shadow-[0_0_30px_rgba(0,0,0,0.5)] ${
                  result.threat ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                }`}>
                  {result.threat ? <ShieldAlert size={64} strokeWidth={1.5} /> : <ShieldCheck size={64} strokeWidth={1.5} />}
                </div>
                
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Threat Status</p>
                  <h4 className={`text-2xl font-bold tracking-tight ${result.threat ? 'text-red-500' : 'text-emerald-500'}`}>
                    {result.threat ? 'THREAT DETECTED' : 'TRAFFIC SAFE'}
                  </h4>
                </div>

                <div className="w-full grid grid-cols-2 gap-3 mt-4">
                  <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-left">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Confidence</p>
                    <p className="text-lg font-mono font-bold text-white">{(result.confidence * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-left">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Threat Type</p>
                    <p className="text-sm font-bold text-white capitalize truncate">{result.threat_type?.replace('_', ' ') || 'Normal'}</p>
                  </div>
                </div>
              </div>
              
              {/* Details & Explanation Column */}
              <div className="lg:w-2/3 space-y-8">
                
                {/* Engine Details */}
                <div>
                  <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Zap size={14} className="text-indigo-400" />
                    Detection Engine Breakdown
                  </h5>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                      <p className="text-xs text-slate-400 mb-1">Random Forest Prediction</p>
                      <p className="font-mono text-sm font-semibold text-slate-200">
                        {result.rf_prediction === 1 ? '1 (Attack)' : result.rf_prediction === 0 ? '0 (Normal)' : result.rf_prediction}
                      </p>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                      <p className="text-xs text-slate-400 mb-1">Isolation Forest Prediction</p>
                      <p className="font-mono text-sm font-semibold text-slate-200">
                        {result.if_prediction === -1 ? '-1 (Anomaly)' : result.if_prediction === 1 ? '1 (Normal)' : result.if_prediction}
                      </p>
                    </div>
                  </div>
                </div>

                {/* SHAP Explanation */}
                <div>
                  <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">AI Explanation (SHAP)</h5>
                  <p className="text-slate-300 text-sm leading-relaxed bg-slate-900/30 p-4 rounded-lg border border-slate-800/50 border-l-2 border-l-indigo-500">
                    {result.explanation}
                  </p>
                </div>
                
                {/* Top Features */}
                {result.top_features && result.top_features.length > 0 && (
                  <div>
                    <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Top Contributing Features</h5>
                    <div className="space-y-3">
                      {result.top_features.map((f: any, idx: number) => {
                        const width = `${Math.max(5, (Math.abs(f.value) / maxFeatureValue) * 100)}%`;
                        const isPositive = f.value > 0;
                        
                        return (
                          <div key={idx} className="flex items-center gap-4 text-sm">
                            <span className="w-32 truncate font-mono text-xs text-slate-400 text-right" title={f.feature}>
                              {f.feature}
                            </span>
                            <div className="flex-1 bg-slate-900/50 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div 
                                className={`h-full rounded-full ${isPositive ? 'bg-indigo-500' : 'bg-blue-500'}`} 
                                style={{ width }}
                              ></div>
                            </div>
                            <span className="w-16 font-mono text-xs font-semibold text-slate-300">
                              {f.value > 0 ? '+' : ''}{f.value.toFixed(4)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Prediction;
