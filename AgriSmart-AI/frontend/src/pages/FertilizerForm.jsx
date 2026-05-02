import { useState } from 'react';
import { fertilizerAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Flower2, Loader2, Leaf, Droplets, ThermometerSun, MapPin, CheckCircle2, XCircle, Languages, BookOpen } from 'lucide-react';
import toast from 'react-hot-toast';

const CROPS = ['Wheat', 'Rice', 'Maize', 'Sugarcane', 'Cotton', 'Tomato', 'Potato', 'Soybean', 'Onion', 'Mustard', 'Barley', 'Groundnut'];
const SOIL_TYPES = ['Sandy', 'Loamy', 'Clay', 'Silty', 'Peaty', 'Chalky', 'Black', 'Red'];
const GROWTH_STAGES = ['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Harvesting'];
const REGIONS = ['Arid', 'Semi-arid', 'Tropical', 'Subtropical', 'Temperate'];

export default function FertilizerForm() {
  const [form, setForm] = useState({ crop: '', soil_type: '', stage: '', problem: '', region: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showHindi, setShowHindi] = useState(false);

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.crop || !form.soil_type || !form.stage || !form.region) {
      toast.error('Please fill in all required fields');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await fertilizerAPI.recommend(form);
      setResult(res.data);
      toast.success('Recommendation ready! 🌱');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to get recommendation');
    } finally {
      setLoading(false);
    }
  };

  const hindi = result?.hindi;

  return (
    <div className="max-w-5xl space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <Flower2 className="w-5 h-5 text-accent" />
          </div>
          Fertilizer Recommendation
        </h1>
        <p className="text-text-secondary text-sm mt-2">Get AI-powered fertilizer advice based on your crop, soil, and conditions</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <form onSubmit={handleSubmit} className="glass-card-static p-6 space-y-4">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-2">Crop Details</h3>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><Leaf className="w-3.5 h-3.5" /> Crop Name *</label>
              <select value={form.crop} onChange={(e) => handleChange('crop', e.target.value)} className="form-select" id="fert-crop">
                <option value="">Select crop</option>
                {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><Droplets className="w-3.5 h-3.5" /> Soil Type *</label>
              <select value={form.soil_type} onChange={(e) => handleChange('soil_type', e.target.value)} className="form-select" id="fert-soil">
                <option value="">Select soil type</option>
                {SOIL_TYPES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><ThermometerSun className="w-3.5 h-3.5" /> Growth Stage *</label>
              <select value={form.stage} onChange={(e) => handleChange('stage', e.target.value)} className="form-select" id="fert-stage">
                <option value="">Select stage</option>
                {GROWTH_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 flex items-center gap-2"><MapPin className="w-3.5 h-3.5" /> Region / Climate *</label>
              <select value={form.region} onChange={(e) => handleChange('region', e.target.value)} className="form-select" id="fert-region">
                <option value="">Select region</option>
                {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 block">Current Problem (Optional)</label>
              <textarea
                value={form.problem}
                onChange={(e) => handleChange('problem', e.target.value)}
                placeholder="e.g., Yellowing leaves, stunted growth..."
                className="form-input min-h-[80px] resize-y"
                id="fert-problem"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full" id="fert-submit">
              {loading ? <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</> : <><Flower2 className="w-5 h-5" /> Get Recommendation</>}
            </button>
          </form>
        </motion.div>

        {/* Result */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="glass-card-static p-6 h-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider">Recommendation</h3>
              {result && !result.error && (
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
              )}
            </div>

            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton-loader h-6 w-full"></div>)}
              </div>
            ) : result && !result.error ? (
              <AnimatePresence>
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
                  {/* Primary Fertilizer */}
                  {result.primary_fertilizer && (
                    <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                      <h4 className="text-lg font-bold text-secondary">{result.primary_fertilizer.name}</h4>
                      {result.primary_fertilizer.commercial_name && (
                        <p className="text-sm text-accent mt-0.5 font-medium">
                          🏷️ {result.primary_fertilizer.commercial_name}
                        </p>
                      )}
                      {showHindi && hindi?.fertilizer_name && (
                        <p className="text-sm text-info mt-1 font-medium">
                          🇮🇳 {hindi.fertilizer_name}
                        </p>
                      )}
                      <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
                        <div><span className="text-text-muted">NPK:</span><span className="text-text-primary ml-1">{result.primary_fertilizer.npk_ratio}</span></div>
                        <div><span className="text-text-muted">Qty:</span><span className="text-text-primary ml-1">{result.primary_fertilizer.quantity_per_acre}</span></div>
                        <div className="col-span-2"><span className="text-text-muted">Cost:</span><span className="text-accent ml-1 font-medium">{result.primary_fertilizer.cost_inr}</span></div>
                      </div>
                    </div>
                  )}

                  {/* Hindi Summary Banner */}
                  {showHindi && hindi?.summary && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="p-3 rounded-lg bg-info/10 border border-info/20"
                    >
                      <p className="text-sm text-info font-medium">📋 {hindi.summary}</p>
                    </motion.div>
                  )}

                  {/* Secondary Nutrients */}
                  {result.secondary_nutrients?.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold text-text-secondary mb-2">Secondary Nutrients</h5>
                      <div className="space-y-2">
                        {result.secondary_nutrients.map((n, i) => (
                          <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-bg-card border border-border-dark">
                            <span className="text-sm text-text-primary">{n.name}</span>
                            <span className="text-xs text-text-muted">{n.quantity} · {n.purpose}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Application */}
                  {result.application_method && (
                    <div>
                      <h5 className="text-sm font-semibold text-text-secondary mb-1">
                        Application Method {showHindi && <span className="text-text-muted font-normal">/ उपयोग विधि</span>}
                      </h5>
                      <p className="text-sm text-text-secondary">{result.application_method}</p>
                      {showHindi && hindi?.method && (
                        <p className="text-sm text-info/80 mt-1">🇮🇳 {hindi.method}</p>
                      )}
                    </div>
                  )}
                  {result.timing && (
                    <div>
                      <h5 className="text-sm font-semibold text-text-secondary mb-1">
                        Timing {showHindi && <span className="text-text-muted font-normal">/ समय</span>}
                      </h5>
                      <p className="text-sm text-text-secondary">{result.timing}</p>
                      {showHindi && hindi?.timing && (
                        <p className="text-sm text-info/80 mt-1">🇮🇳 {hindi.timing}</p>
                      )}
                    </div>
                  )}

                  {/* Organic Alternative */}
                  {result.organic_alternative && (
                    <div className="p-3 rounded-lg bg-secondary/5 border border-secondary/20">
                      <h5 className="text-sm font-semibold text-secondary mb-1">🌿 Organic Alternative</h5>
                      <p className="text-sm text-text-secondary">{result.organic_alternative}</p>
                    </div>
                  )}

                  {/* Do's and Don'ts */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {result.dos?.length > 0 && (
                      <div>
                        <h5 className="text-sm font-semibold text-secondary mb-2 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Do's</h5>
                        <ul className="space-y-1">
                          {result.dos.map((d, i) => <li key={i} className="text-xs text-text-secondary">✅ {d}</li>)}
                          {showHindi && hindi?.dos?.map((d, i) => <li key={`hi-${i}`} className="text-xs text-info/70">✅ {d}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.donts?.length > 0 && (
                      <div>
                        <h5 className="text-sm font-semibold text-danger mb-2 flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> Don'ts</h5>
                        <ul className="space-y-1">
                          {result.donts.map((d, i) => <li key={i} className="text-xs text-text-secondary">❌ {d}</li>)}
                          {showHindi && hindi?.donts?.map((d, i) => <li key={`hi-${i}`} className="text-xs text-info/70">❌ {d}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>

                  {result.expected_improvement && (
                    <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
                      <h5 className="text-sm font-semibold text-accent mb-1">Expected Improvement</h5>
                      <p className="text-sm text-text-secondary">{result.expected_improvement}</p>
                      {showHindi && hindi?.improvement && (
                        <p className="text-sm text-info/80 mt-1">🇮🇳 {hindi.improvement}</p>
                      )}
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Flower2 className="w-16 h-16 text-text-muted/30 mb-4" />
                <p className="text-text-muted">Fill the form and get AI-powered fertilizer advice</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* ── Information Section ── */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card-static p-6 mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
          {/* English Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-green-500" /> About Fertilizer Recommendation
            </h3>
            <div>
              <p className="font-semibold text-green-400">How to use:</p>
              <p>Select your crop, soil type, crop growth stage, and your region. Optionally, describe any current problems your crop is facing. Submit the form to get an AI-generated fertilizer plan.</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">Why it is productive:</p>
              <p>Avoids over-fertilization, saves money, protects soil health, and maximizes crop yield by providing the precise nutrients your plants need right now.</p>
            </div>
          </div>

          {/* Hindi Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <Languages className="w-5 h-5 text-green-500" /> उर्वरक अनुशंसा के बारे में
            </h3>
            <div>
              <p className="font-semibold text-green-400">उपयोग कैसे करें (How to use):</p>
              <p>अपनी फसल, मिट्टी का प्रकार, फसल के विकास का चरण और अपने क्षेत्र का चयन करें। वैकल्पिक रूप से, अपनी फसल की मौजूदा समस्याओं का वर्णन करें। AI-आधारित उर्वरक योजना प्राप्त करने के लिए फॉर्म जमा करें।</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">यह कैसे फायदेमंद है (Why it is productive):</p>
              <p>जरूरत से ज्यादा उर्वरक के उपयोग से बचाता है, पैसे बचाता है, मिट्टी के स्वास्थ्य की रक्षा करता है, और पौधों को आवश्यक पोषक तत्व प्रदान करके फसल की पैदावार को अधिकतम करता है।</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
