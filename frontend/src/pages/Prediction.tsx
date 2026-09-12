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

  const explanationData = result?.explanation 
    ? (typeof result.explanation === 'string' && result.explanation.startsWith('{') ? JSON.parse(result.explanation) : { text: result.explanation, top_features: result.top_features || [] })
    : { text: '', top_features: [] };

  const maxFeatureValue = explanationData.top_features?.length > 0
    ? Math.max(...explanationData.top_features.map((f: any) => Math.abs(f.impact || f.value || 0)))
    : 1;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-5xl mx-auto">
      <div className="border-b border-[#49769F]/30 pb-5">
        <h2 className="text-3xl font-bold text-white tracking-tight">Threat Analysis Engine</h2>
        <p className="text-[#6EA2B3] mt-1">Run active packet analysis using the hybrid ML pipeline.</p>
      </div>
      
      <div className="glass-card p-8 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-[#7BBDE8]"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <h3 className="font-bold text-white text-lg flex items-center gap-2">
              <Network size={20} className="text-[#7BBDE8]" />
              Analyze Offline Packet
            </h3>
            <p className="text-[#BDD8E9] text-sm leading-relaxed">
              Test the Sentinel hybrid ML engine with a real 69-feature network packet captured from the dataset. 
              This sample tests the <strong>production XGBoost model</strong> without applying temporal behavioral correlation.
            </p>
          </div>
          
          <button 
            onClick={handleTestPrediction}
            disabled={loading}
            className="flex items-center justify-center gap-2 bg-[#0A4174]/80 hover:bg-[#49769F]/80 text-white px-8 py-4 rounded-xl font-bold transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(123,189,232,0.15)] border border-[#7BBDE8]/30 min-w-[220px]"
          >
            {loading ? (
              <Activity className="animate-spin text-[#7BBDE8]" size={20} />
            ) : (
              <Play size={20} className="text-[#7BBDE8]" fill="currentColor" />
            )}
            {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-6 rounded-xl flex items-start gap-4 backdrop-blur-sm">
          <ShieldAlert className="mt-0.5 shrink-0 text-red-400" size={20} />
          <div>
            <h4 className="font-bold mb-1 text-red-300">Analysis Failed</h4>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="flex items-center gap-3">
            <Cpu size={24} className="text-[#6EA2B3]" />
            <h3 className="text-xl font-bold text-white tracking-wide">Analysis Results</h3>
          </div>
          
          <div className={`p-8 rounded-xl border shadow-lg relative overflow-hidden backdrop-blur-md ${
            result.threat ? 'bg-[#001D39]/80 border-red-500/30' : 'bg-[#001D39]/80 border-emerald-500/30'
          }`}>
            <div className={`absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl opacity-10 pointer-events-none ${
              result.threat ? 'bg-red-500' : 'bg-emerald-500'
            }`}></div>

            <div className="flex flex-col lg:flex-row gap-10 relative z-10">
              
              <div className="lg:w-1/3 flex flex-col items-center justify-center text-center space-y-4 border-b lg:border-b-0 lg:border-r border-[#49769F]/30 pb-8 lg:pb-0 lg:pr-8">
                <div className={`p-5 rounded-full shadow-[0_0_30px_rgba(0,0,0,0.3)] ${
                  result.threat ? 'bg-red-500/10 text-red-400 border border-red-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {result.threat ? <ShieldAlert size={64} strokeWidth={1.5} /> : <ShieldCheck size={64} strokeWidth={1.5} />}
                </div>
                
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-[#6EA2B3] mb-1">Threat Status</p>
                  <h4 className={`text-2xl font-black tracking-tight ${result.threat ? 'text-red-400' : 'text-emerald-400'}`}>
                    {result.threat ? 'THREAT DETECTED' : 'TRAFFIC SAFE'}
                  </h4>
                </div>

                <div className="w-full grid grid-cols-2 gap-3 mt-4">
                  <div className="bg-[#0A4174]/40 p-3 rounded-lg border border-[#49769F]/30 text-left">
                    <p className="text-[10px] text-[#6EA2B3] uppercase font-bold tracking-wider mb-1">Confidence</p>
                    <p className="text-lg font-mono font-bold text-white">{(result.confidence * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-[#0A4174]/40 p-3 rounded-lg border border-[#49769F]/30 text-left">
                    <p className="text-[10px] text-[#6EA2B3] uppercase font-bold tracking-wider mb-1">Threat Type</p>
                    <p className="text-sm font-bold text-white capitalize truncate">{result.threat_type?.replace('_', ' ') || 'Normal'}</p>
                  </div>
                </div>
              </div>
              
              <div className="lg:w-2/3 space-y-8">
                <div>
                  <h5 className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Zap size={14} className="text-[#7BBDE8]" />
                    Detection Engine Breakdown
                  </h5>
                  <div className="bg-[#0A4174]/40 p-4 rounded-lg border border-[#49769F]/30">
                    <p className="text-xs text-[#6EA2B3] mb-1">XGBoost Production Model Prediction</p>
                    <p className="font-mono text-sm font-semibold text-[#BDD8E9]">
                      {result.threat ? '1 (Attack)' : '0 (Normal)'}
                    </p>
                  </div>
                </div>

                <div>
                  <h5 className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider mb-3">AI Explanation (SHAP)</h5>
                  <p className="text-[#BDD8E9] text-sm leading-relaxed bg-[#0A4174]/20 p-4 rounded-lg border border-[#49769F]/30 border-l-2 border-l-[#7BBDE8]">
                    {explanationData.text}
                  </p>
                </div>
                
                {explanationData.top_features && explanationData.top_features.length > 0 && (
                  <div>
                    <h5 className="text-xs font-bold text-[#6EA2B3] uppercase tracking-wider mb-4">Top Contributing Features</h5>
                    <div className="space-y-3">
                      {explanationData.top_features.map((f: any, idx: number) => {
                        const val = f.impact || f.value || 0;
                        const width = `${Math.max(5, (Math.abs(val) / maxFeatureValue) * 100)}%`;
                        const isPositive = val > 0;
                        
                        return (
                          <div key={idx} className="flex items-center gap-4 text-sm">
                            <span className="w-32 truncate font-mono text-xs text-[#6EA2B3] text-right" title={f.feature}>
                              {f.feature}
                            </span>
                            <div className="flex-1 bg-[#0A4174]/40 rounded-full h-2 overflow-hidden border border-[#49769F]/20">
                              <div 
                                className={`h-full rounded-full ${isPositive ? 'bg-[#7BBDE8]' : 'bg-[#4E8EA2]'}`} 
                                style={{ width }}
                              ></div>
                            </div>
                            <span className="w-16 font-mono text-xs font-semibold text-[#BDD8E9]">
                              {val > 0 ? '+' : ''}{val.toFixed(4)}
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
