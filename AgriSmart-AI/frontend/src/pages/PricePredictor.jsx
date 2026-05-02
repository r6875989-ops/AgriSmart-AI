import { useState } from 'react';
import { priceAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Loader2, ArrowUpRight, ArrowDownRight, Minus, IndianRupee, Calendar, MapPin, XCircle, Leaf, Languages, BookOpen } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import toast from 'react-hot-toast';

const CROPS = ['Wheat', 'Rice', 'Maize', 'Sugarcane', 'Cotton', 'Tomato', 'Potato', 'Soybean', 'Onion', 'Mustard', 'Groundnut', 'Chana'];
const STATES = [
  'Andhra Pradesh', 'Bihar', 'Chhattisgarh', 'Gujarat', 'Haryana', 'Himachal Pradesh',
  'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha',
  'Punjab', 'Rajasthan', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
];

export default function PricePredictor() {
  const [crop, setCrop] = useState('');
  const [state, setState] = useState('');
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showHindi, setShowHindi] = useState(false);

  const currentMonth = new Date().toLocaleDateString('en-IN', { month: 'long' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!crop || !state) {
      toast.error('Please select crop and state');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await priceAPI.predict({ crop, state, month: currentMonth, quantity: quantity || null });
      setResult(res.data);
      toast.success('Price prediction ready! 📈');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to get prediction');
    } finally {
      setLoading(false);
    }
  };

  const trendIcon = {
    rising: <ArrowUpRight className="w-5 h-5 text-secondary" />,
    falling: <ArrowDownRight className="w-5 h-5 text-danger" />,
    stable: <Minus className="w-5 h-5 text-text-muted" />,
  };

  const trendColor = {
    rising: 'text-secondary',
    falling: 'text-danger',
    stable: 'text-text-muted',
  };

  // Build chart data from result
  const getChartData = () => {
    if (!result) return [];
    if (result.price_history?.length > 0) {
      return result.price_history;
    }
    // Fallback: create simple data from predictions
    return [
      { month: 'Current Min', price: result.current_price_min },
      { month: 'Current Max', price: result.current_price_max },
      { month: '30-day', price: result.predicted_30_days },
      { month: '60-day', price: result.predicted_60_days },
    ];
  };

  return (
    <div className="max-w-5xl space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-info/10 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-info" />
          </div>
          Market Price Prediction
        </h1>
        <p className="text-text-secondary text-sm mt-2">Get AI-powered market price forecasts for Indian crops</p>
      </motion.div>

      {/* Form */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <form onSubmit={handleSubmit} className="glass-card-static p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><Leaf className="w-3.5 h-3.5" /> Crop *</label>
              <select value={crop} onChange={(e) => setCrop(e.target.value)} className="form-select" id="price-crop">
                <option value="">Select crop</option>
                {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><MapPin className="w-3.5 h-3.5" /> State *</label>
              <select value={state} onChange={(e) => setState(e.target.value)} className="form-select" id="price-state">
                <option value="">Select state</option>
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><Calendar className="w-3.5 h-3.5" /> Month</label>
              <input type="text" value={currentMonth} disabled className="form-input opacity-70" />
            </div>
            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><IndianRupee className="w-3.5 h-3.5" /> Qty (quintals)</label>
              <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="Optional" className="form-input" id="price-qty" />
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn-primary mt-4" id="price-submit">
            {loading ? <><Loader2 className="w-5 h-5 animate-spin" /> Predicting...</> : <><TrendingUp className="w-5 h-5" /> Get Prediction</>}
          </button>
        </form>
      </motion.div>

      {/* Results */}
      {loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="skeleton-loader h-32"></div>)}
          <div className="lg:col-span-3 skeleton-loader h-64"></div>
        </div>
      )}

      {result && result.error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card-static p-6 border-danger/30 text-center">
          <XCircle className="w-12 h-12 text-danger mx-auto mb-3" />
          <h3 className="text-lg font-bold text-danger mb-1">Prediction Failed</h3>
          <p className="text-text-secondary">{result.error}</p>
          <p className="text-sm text-text-muted mt-4">Please check your NVIDIA API Key in the backend/.env file.</p>
        </motion.div>
      )}

      {result && !result.error && (
        <AnimatePresence>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* Price Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="stat-card">
                <p className="text-xs text-text-muted uppercase">Current Market Price</p>
                <p className="text-2xl font-bold text-text-primary mt-1">₹{result.current_price_min}-{result.current_price_max}</p>
                <p className="text-xs text-text-muted mt-1">per quintal</p>
                {showHindi && result.hindi?.current_price && (
                  <p className="text-xs text-info mt-1">{result.hindi.current_price}</p>
                )}
              </div>
              <div className="stat-card">
                <p className="text-xs text-text-muted uppercase">30-Day Forecast</p>
                <p className="text-2xl font-bold text-secondary mt-1">₹{result.predicted_30_days}</p>
                <p className="text-xs text-text-muted mt-1">predicted</p>
                {showHindi && result.hindi?.predicted_30 && (
                  <p className="text-xs text-info mt-1">{result.hindi.predicted_30}</p>
                )}
              </div>
              <div className="stat-card">
                <p className="text-xs text-text-muted uppercase">60-Day Forecast</p>
                <p className="text-2xl font-bold text-accent mt-1">₹{result.predicted_60_days}</p>
                <p className="text-xs text-text-muted mt-1">predicted</p>
                {showHindi && result.hindi?.predicted_60 && (
                  <p className="text-xs text-info mt-1">{result.hindi.predicted_60}</p>
                )}
              </div>
              <div className="stat-card">
                <p className="text-xs text-text-muted uppercase">Market Trend</p>
                <div className="flex items-center gap-2 mt-1">
                  {trendIcon[result.trend] || trendIcon.stable}
                  <p className={`text-2xl font-bold capitalize ${trendColor[result.trend] || 'text-text-muted'}`}>{result.trend}</p>
                </div>
                {result.msp && <p className="text-xs text-text-muted mt-1">MSP: ₹{result.msp}</p>}
                {showHindi && result.hindi?.trend && (
                  <p className="text-xs text-info mt-1">रुझान: {result.hindi.trend}</p>
                )}
              </div>
            </div>

            {/* Chart */}
            <div className="glass-card-static p-6">
              <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">Price Trend Chart</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={getChartData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3A423A" />
                    <XAxis dataKey="month" stroke="#6B736B" fontSize={12} />
                    <YAxis stroke="#6B736B" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: '#232923', border: '1px solid #3A423A', borderRadius: '12px', color: '#E8E8E8' }}
                      formatter={(value) => [`₹${value}`, 'Price']}
                    />
                    {result.msp && <ReferenceLine y={result.msp} stroke="#F4A261" strokeDasharray="5 5" label={{ value: `MSP: ₹${result.msp}`, fill: '#F4A261', fontSize: 11 }} />}
                    <Line type="monotone" dataKey="price" stroke="#52B788" strokeWidth={3} dot={{ fill: '#52B788', r: 5 }} activeDot={{ r: 7 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Advice + Factors */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="glass-card-static p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider">Trading Advice</h3>
                  <button
                    onClick={() => setShowHindi(!showHindi)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${showHindi
                        ? 'bg-accent/20 text-accent border border-accent/30'
                        : 'bg-bg-card text-text-secondary hover:bg-primary/10 border border-border-dark'
                      }`}
                  >
                    <Languages className="w-3.5 h-3.5" />
                    {showHindi ? 'English' : 'हिंदी'}
                  </button>
                </div>
                <p className="text-sm text-text-secondary">{result.advice}</p>
                {showHindi && result.hindi?.summary && (
                  <p className="text-sm text-info mt-2">🇮🇳 {result.hindi.summary}</p>
                )}
                {result.best_sell_window && (
                  <div className="mt-4 p-3 rounded-lg bg-secondary/10 border border-secondary/20">
                    <p className="text-sm font-medium text-secondary">Best Sell Window: {result.best_sell_window}</p>
                  </div>
                )}
                {showHindi && result.hindi?.msp && (
                  <div className="mt-3 p-2.5 rounded-lg bg-info/10 border border-info/20">
                    <p className="text-sm text-info font-medium">{result.hindi.msp}</p>
                  </div>
                )}
              </div>
              {result.factors?.length > 0 && (
                <div className="glass-card-static p-6">
                  <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-3">Key Factors</h3>
                  <ul className="space-y-2">
                    {result.factors.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0"></span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      )}

      {/* ── Information Section ── */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card-static p-6 mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
          {/* English Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-green-500" /> About Market Price Prediction
            </h3>
            <div>
              <p className="font-semibold text-green-400">How to use:</p>
              <p>Select the specific crop and the state where you intend to sell. Provide the month to get a 30-day and 60-day price forecast and market trends.</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">Why it is productive:</p>
              <p>Empowers farmers to make informed selling decisions. By understanding price trends and MSP, you can hold or sell your stock at the right time to maximize your profit.</p>
            </div>
          </div>

          {/* Hindi Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <Languages className="w-5 h-5 text-green-500" /> बाज़ार मूल्य भविष्यवाणी के बारे में
            </h3>
            <div>
              <p className="font-semibold text-green-400">उपयोग कैसे करें (How to use):</p>
              <p>उस विशिष्ट फसल और राज्य का चयन करें जहाँ आप बेचना चाहते हैं। 30-दिन और 60-दिन का मूल्य पूर्वानुमान और बाज़ार के रुझान जानने के लिए महीने का विवरण दें।</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">यह कैसे फायदेमंद है (Why it is productive):</p>
              <p>किसानों को बेचने के बारे में सही निर्णय लेने के लिए सशक्त बनाता है। मूल्य के रुझान और न्यूनतम समर्थन मूल्य (MSP) को समझकर, आप अधिकतम लाभ प्राप्त करने के लिए सही समय पर अपना स्टॉक रोक या बेच सकते हैं।</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

