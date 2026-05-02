import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI } from '../services/api';
import { motion } from 'framer-motion';
import {
  Scan, Flower2, TrendingUp, Mic, CheckCircle2, AlertTriangle,
  Clock, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('disease');
  const [history, setHistory] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    loadHistory(activeTab);
  }, [activeTab]);

  const loadDashboard = async () => {
    try {
      const [statsRes, activityRes] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getRecentActivity(),
      ]);
      setStats(statsRes.data);
      setActivities(activityRes.data.activities || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async (module) => {
    try {
      const res = await dashboardAPI.getHistory(module);
      setHistory(res.data.history || []);
    } catch (err) {
      console.error('Failed to load history:', err);
      setHistory([]);
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return '';
    const now = new Date();
    const date = new Date(timestamp);
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)} days ago`;
  };

  const getSeasonName = () => {
    const month = new Date().getMonth();
    if (month >= 5 && month <= 9) return 'Kharif Season';
    if (month >= 10 || month <= 1) return 'Rabi Season';
    return 'Zaid Season';
  };

  const activityIcons = {
    disease: <Scan className="w-4 h-4" />,
    fertilizer: <Flower2 className="w-4 h-4" />,
    price: <TrendingUp className="w-4 h-4" />,
    voice: <Mic className="w-4 h-4" />,
  };

  const activityColors = {
    disease: 'text-secondary bg-secondary/10',
    fertilizer: 'text-accent bg-accent/10',
    price: 'text-info bg-info/10',
    voice: 'text-primary-light bg-primary/10',
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton-loader h-24 w-full"></div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton-loader h-28"></div>)}
        </div>
        <div className="skeleton-loader h-64 w-full"></div>
      </div>
    );
  }



  return (
    <div className="space-y-6 max-w-7xl">
      {/* Welcome Banner */}
      <motion.div {...fadeInUp} transition={{ delay: 0 }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-text-primary">
              Namaste, {user?.name?.split(' ')[0]} Ji! <span className="inline-block animate-float">🌾</span>
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              {getSeasonName()} · {new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
            </p>
          </div>
          <span className="badge badge-success self-start sm:self-auto">Account active</span>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div {...fadeInUp} transition={{ delay: 0.1 }} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total scans', value: stats?.total_scans || 0, sub: `+${stats?.scans_this_week || 0} this week`, subColor: 'text-secondary', icon: Scan },
          { label: 'Diseases found', value: stats?.diseases_found || 0, sub: stats?.diseases_found > 0 ? `${stats.diseases_found} detected` : 'None yet', subColor: 'text-warning', icon: AlertTriangle },
          { label: 'Price queries', value: stats?.price_checks || 0, sub: 'Market insights', subColor: 'text-info', icon: TrendingUp },
          { label: 'Voice sessions', value: stats?.voice_sessions || 0, sub: 'Hindi', subColor: 'text-accent', icon: Mic },
        ].map((stat, i) => (
          <div key={i} className="stat-card">
            <p className="text-xs text-text-muted font-medium uppercase tracking-wide">{stat.label}</p>
            <p className="text-3xl font-bold text-text-primary mt-1">{stat.value}</p>
            <p className={`text-xs mt-2 ${stat.subColor}`}>{stat.sub}</p>
          </div>
        ))}
      </motion.div>

      {/* Two Column: Activity + Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <motion.div {...fadeInUp} transition={{ delay: 0.2 }} className="glass-card-static p-6">
          <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {activities.length === 0 ? (
              <p className="text-text-muted text-sm py-8 text-center">No activity yet. Start by scanning a crop! 🌿</p>
            ) : (
              activities.slice(0, 5).map((act, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${activityColors[act.type] || 'text-text-muted bg-bg-card'}`}>
                    {activityIcons[act.type]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-text-primary">{act.title}</p>
                      <span className="text-xs text-text-muted flex-shrink-0 ml-2">{formatTimeAgo(act.timestamp)}</span>
                    </div>
                    <p className="text-xs text-text-secondary mt-0.5 truncate">{act.subtitle}</p>
                    {act.detail && act.type === 'disease' && (
                      <span className="badge badge-warning text-[10px] mt-1 inline-block">{act.detail}</span>
                    )}
                    {act.detail && act.type === 'fertilizer' && (
                      <span className="badge badge-success text-[10px] mt-1 inline-block">{act.detail}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* Quick Stats Panel */}
        <motion.div {...fadeInUp} transition={{ delay: 0.3 }} className="space-y-6">
          {/* Crop Predictions */}
          <div className="glass-card-static p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">My Crop Predictions</h3>
            {activities.filter(a => a.type === 'price').length === 0 ? (
              <p className="text-text-muted text-sm py-4 text-center">No predictions yet</p>
            ) : (
              <div className="space-y-3">
                {activities.filter(a => a.type === 'price').slice(0, 3).map((pred, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border-dark last:border-0">
                    <div>
                      <p className="text-sm font-medium text-text-primary">{pred.subtitle?.split('·')[0]?.trim()}</p>
                      <p className="text-xs text-text-muted">{pred.subtitle}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-secondary">{pred.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Saved Fertilizer Plans */}
          <div className="glass-card-static p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">Saved Fertilizer Plans</h3>
            {activities.filter(a => a.type === 'fertilizer').length === 0 ? (
              <p className="text-text-muted text-sm py-4 text-center">No plans saved yet</p>
            ) : (
              <div className="space-y-3">
                {activities.filter(a => a.type === 'fertilizer').slice(0, 3).map((fert, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border-dark last:border-0">
                    <p className="text-sm text-text-primary">{fert.subtitle}</p>
                    <span className="badge badge-success text-[10px]">{fert.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* History Tabs */}
      <motion.div {...fadeInUp} transition={{ delay: 0.4 }} className="glass-card-static p-6">
        <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">Disease Scan History</h3>

        {/* Tab Buttons */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { key: 'disease', label: 'Disease Scans', icon: Scan },
            { key: 'fertilizer', label: 'Fertilizer', icon: Flower2 },
            { key: 'price', label: 'Price History', icon: TrendingUp },
            { key: 'voice', label: 'Voice Logs', icon: Mic },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${activeTab === tab.key
                  ? 'bg-primary/20 text-secondary border border-primary/30'
                  : 'text-text-secondary hover:bg-bg-card border border-transparent'
                }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* History Table */}
        {history.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-text-muted">No {activeTab} history yet.</p>
            <p className="text-text-muted text-sm mt-1">Start using the {activeTab} module to see results here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {activeTab === 'disease' && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-dark">
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Crop</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Disease detected</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Confidence</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Status</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, i) => (
                    <tr key={i} className="border-b border-border-dark/50 hover:bg-bg-card/50 transition-colors">
                      <td className="py-3 px-2 font-medium text-text-primary">{item.affected_crop || 'Unknown'}</td>
                      <td className="py-3 px-2">
                        <span className={`badge text-[11px] ${item.is_healthy ? 'badge-success' : 'badge-warning'}`}>
                          {item.disease || 'Unknown'}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-text-secondary">{item.confidence}%</td>
                      <td className="py-3 px-2">
                        <span className={`badge text-[11px] ${item.is_healthy ? 'badge-success' : 'badge-info'}`}>
                          {item.is_healthy ? 'No action' : 'In treatment'}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-text-muted">{formatDate(item.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'fertilizer' && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-dark">
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Crop</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Soil</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Fertilizer</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Quantity</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, i) => (
                    <tr key={i} className="border-b border-border-dark/50 hover:bg-bg-card/50 transition-colors">
                      <td className="py-3 px-2 font-medium text-text-primary">{item.crop}</td>
                      <td className="py-3 px-2 text-text-secondary">{item.soil_type}</td>
                      <td className="py-3 px-2"><span className="badge badge-success text-[11px]">{item.fertilizer}</span></td>
                      <td className="py-3 px-2 text-text-secondary">{item.quantity}</td>
                      <td className="py-3 px-2 text-text-muted">{formatDate(item.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'price' && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-dark">
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Crop</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">State</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Current Price</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Predicted</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Trend</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, i) => (
                    <tr key={i} className="border-b border-border-dark/50 hover:bg-bg-card/50 transition-colors">
                      <td className="py-3 px-2 font-medium text-text-primary">{item.crop}</td>
                      <td className="py-3 px-2 text-text-secondary">{item.state}</td>
                      <td className="py-3 px-2 text-text-secondary">{item.current_price}</td>
                      <td className="py-3 px-2 text-secondary font-medium">{item.predicted_price}</td>
                      <td className="py-3 px-2">
                        {item.trend === 'rising' && <span className="flex items-center gap-1 text-secondary"><ArrowUpRight className="w-3 h-3" />Rising</span>}
                        {item.trend === 'falling' && <span className="flex items-center gap-1 text-danger"><ArrowDownRight className="w-3 h-3" />Falling</span>}
                        {item.trend === 'stable' && <span className="flex items-center gap-1 text-text-muted"><Minus className="w-3 h-3" />Stable</span>}
                      </td>
                      <td className="py-3 px-2 text-text-muted">{formatDate(item.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'voice' && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-dark">
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Query</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Intent</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Module</th>
                    <th className="text-left py-3 px-2 text-text-muted font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, i) => (
                    <tr key={i} className="border-b border-border-dark/50 hover:bg-bg-card/50 transition-colors">
                      <td className="py-3 px-2 text-text-primary max-w-xs truncate">{item.transcript}</td>
                      <td className="py-3 px-2"><span className="badge badge-info text-[11px]">{item.intent}</span></td>
                      <td className="py-3 px-2 text-text-secondary">{item.module_triggered}</td>
                      <td className="py-3 px-2 text-text-muted">{formatDate(item.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}

