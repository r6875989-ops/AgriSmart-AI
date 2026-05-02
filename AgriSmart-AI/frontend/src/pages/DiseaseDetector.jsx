import { useState, useRef } from 'react';
import { diseaseAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Scan, AlertTriangle, CheckCircle2,
  Shield, Loader2, X, Image, ChevronDown, ChevronUp,
  BookOpen, Leaf, Star, Languages
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Constants ────────────────────────────────────────────────────────────────
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE_MB = 5;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

const SEVERITY_STYLES = {
  High: { badge: 'bg-red-100 text-red-700 border border-red-200', dot: 'bg-red-500' },
  Medium: { badge: 'bg-yellow-100 text-yellow-700 border border-yellow-200', dot: 'bg-yellow-500' },
  Low: { badge: 'bg-blue-100 text-blue-700 border border-blue-200', dot: 'bg-blue-500' },
  None: { badge: 'bg-green-100 text-green-700 border border-green-200', dot: 'bg-green-500' },
  Unknown: { badge: 'bg-gray-100 text-gray-600 border border-gray-200', dot: 'bg-gray-400' },
};

// ─── Sub-components ───────────────────────────────────────────────────────────
function ProgressBar({ label, value, color = 'bg-green-500' }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span>{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

function SectionList({ items, icon: Icon, iconClass = 'text-green-500' }) {
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
          {Icon
            ? <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${iconClass}`} />
            : <span className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${iconClass}`} />
          }
          {item}
        </li>
      ))}
    </ul>
  );
}

function SkeletonLoader() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-7 bg-gray-200 rounded-lg w-3/4" />
      <div className="h-4 bg-gray-200 rounded w-1/2" />
      <div className="h-px bg-gray-100 w-full" />
      <div className="space-y-2">
        {[1, 2, 3].map(i => <div key={i} className="h-4 bg-gray-200 rounded w-full" />)}
      </div>
      <div className="h-4 bg-gray-200 rounded w-2/3" />
      <div className="h-20 bg-gray-200 rounded-lg w-full" />
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function DiseaseDetector() {
  const [image, setImage] = useState(null);   // File object
  const [preview, setPreview] = useState(null);   // data URL for <img>
  const [dataURL, setDataURL] = useState(null);   // full data URL sent to backend
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [showTop3, setShowTop3] = useState(false);
  const [showHindi, setShowHindi] = useState(false);
  const fileInputRef = useRef(null);

  // ── File validation & loading ──────────────────────────────────────────────
  const handleFile = (file) => {
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.error('Only JPG, PNG, or WebP images are allowed');
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      toast.error(`Image must be under ${MAX_SIZE_MB}MB`);
      return;
    }

    setImage(file);
    setResult(null);
    setShowTop3(false);

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);   // for <img src>
      setDataURL(e.target.result);   // full "data:image/jpeg;base64,..." — sent to backend
    };
    reader.onerror = () => toast.error('Failed to read image file');
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const clearAll = () => {
    setImage(null);
    setPreview(null);
    setDataURL(null);
    setResult(null);
    setShowTop3(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── Prediction call ────────────────────────────────────────────────────────
  const handleDetect = async () => {
    if (!image || !dataURL) {
      toast.error('Please upload a leaf image first');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // FIX: send full dataURL — backend strips "data:image/...;base64," prefix
      const res = await diseaseAPI.predict(dataURL, image.name);
      setResult(res.data);
      toast.success('Analysis complete!');
    } catch (err) {
      const msg = err.response?.data?.error || 'Analysis failed. Please try again.';
      toast.error(msg);
      console.error('[DiseaseDetector] predict error:', err);
    } finally {
      setLoading(false);
    }
  };

  // ── Helpers ────────────────────────────────────────────────────────────────
  const severityStyle = SEVERITY_STYLES[result?.severity] || SEVERITY_STYLES.Unknown;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto space-y-6 p-4">

      {/* ── Page Header ── */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-green-50 border border-green-100 flex items-center justify-center">
            <Leaf className="w-5 h-5 text-green-600" />
          </div>
          <h1 className="text-2xl font-semibold text-gray-800">Crop Disease Detection</h1>
        </div>
        <p className="text-gray-500 text-sm ml-13 pl-1">
          Upload a leaf photo — our CNN model (MobileNetV2, 96% accuracy) detects 15 disease classes instantly.
        </p>
      </motion.div>

      {/* ── Model Info Strip ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap gap-3"
      >
        {[
          { label: 'Model', value: 'MobileNetV2' },
          { label: 'Dataset', value: 'PlantVillage' },
          { label: 'Classes', value: '15 diseases' },
          { label: 'Accuracy', value: '96.0%' },
        ].map(({ label, value }) => (
          <div key={label} className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
            <span className="text-xs text-gray-400">{label}:</span>
            <span className="text-xs font-medium text-gray-700">{value}</span>
          </div>
        ))}
      </motion.div>

      {/* ── Two-column layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ════ LEFT: Upload Panel ════ */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <div className="bg-white border border-gray-200 rounded-2xl p-6 h-full flex flex-col">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Upload leaf image
            </h3>

            {/* Drop zone / preview */}
            {!preview ? (
              <div
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center
                  cursor-pointer transition-all min-h-[280px] gap-4
                  ${dragOver
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-200 hover:border-green-300 hover:bg-green-50/40'}
                `}
              >
                <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center">
                  <Upload className="w-7 h-7 text-gray-300" />
                </div>
                <div className="text-center space-y-1">
                  <p className="text-sm font-medium text-gray-600">Drop your leaf image here</p>
                  <p className="text-xs text-gray-400">or click to browse</p>
                  <p className="text-xs text-gray-300 mt-2">JPG · PNG · WebP · Max {MAX_SIZE_MB}MB</p>
                </div>
              </div>
            ) : (
              <div className="flex-1 space-y-3">
                <div className="relative rounded-xl overflow-hidden border border-gray-100">
                  <img
                    src={preview}
                    alt="Leaf preview"
                    className="w-full h-64 object-cover"
                  />
                  <button
                    onClick={clearAll}
                    className="absolute top-2 right-2 w-8 h-8 bg-black/50 hover:bg-black/70 rounded-lg flex items-center justify-center transition-colors"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                  <div className="absolute bottom-2 left-2 bg-black/50 rounded-md px-2 py-1">
                    <p className="text-xs text-white truncate max-w-[200px]">{image?.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                  Image ready — {(image?.size / 1024).toFixed(0)} KB
                </div>
              </div>
            )}

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              onChange={(e) => handleFile(e.target.files[0])}
              className="hidden"
            />

            {/* Detect button */}
            <button
              onClick={handleDetect}
              disabled={!image || loading}
              className={`
                mt-4 w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all
                ${!image || loading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white shadow-sm active:scale-[0.98]'}
              `}
            >
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" />Analysing...</>
                : <><Scan className="w-4 h-4" />Detect Disease</>
              }
            </button>

            {/* Photo tips */}
            <div className="mt-4 p-3 bg-amber-50 border border-amber-100 rounded-xl">
              <p className="text-xs font-medium text-amber-700 mb-2">Photo tips for best accuracy</p>
              <ul className="space-y-1">
                {[
                  'Use good natural daylight',
                  'Fill the frame with the leaf',
                  'Avoid blurry or dark shots',
                  'Show the affected area clearly',
                ].map((tip) => (
                  <li key={tip} className="text-xs text-amber-600 flex items-center gap-1.5">
                    <Star className="w-3 h-3 flex-shrink-0" />{tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>

        {/* ════ RIGHT: Result Panel ════ */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="bg-white border border-gray-200 rounded-2xl p-6 h-full flex flex-col">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Analysis result
            </h3>

            {/* Loading skeleton */}
            {loading && <SkeletonLoader />}

            {/* Empty state */}
            {!loading && !result && (
              <div className="flex-1 flex flex-col items-center justify-center py-16 text-center gap-3">
                <Image className="w-14 h-14 text-gray-200" />
                <p className="text-sm text-gray-400">Upload a leaf image and click "Detect Disease"</p>
                <p className="text-xs text-gray-300">The AI will analyse for disease patterns</p>
              </div>
            )}

            {/* Result */}
            <AnimatePresence>
              {!loading && result && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-5 flex-1"
                >
                  {/* ── Disease name + status ── */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {result.is_healthy
                          ? <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                          : <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                        }
                        <h4 className="text-lg font-semibold text-gray-800 leading-tight">
                          {result.disease_name}
                        </h4>
                      </div>
                      {result.hindi?.disease_name && (
                        <p className="text-sm text-blue-600 ml-7 font-medium">
                          🇮🇳 {result.hindi.disease_name}
                        </p>
                      )}
                      <p className="text-sm text-gray-500 ml-7">
                        Crop: <span className="font-medium text-gray-700">{result.affected_crop}</span>
                        {result.hindi?.crop && (
                          <span className="text-blue-500 ml-1">({result.hindi.crop})</span>
                        )}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-2xl font-bold text-green-600">{result.confidence}%</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${severityStyle.badge}`}>
                        {result.severity} severity
                      </span>
                      {result.hindi?.severity && (
                        <p className="text-xs text-blue-500 mt-1">गंभीरता: {result.hindi.severity}</p>
                      )}
                    </div>
                  </div>

                  {/* Hindi status banner */}
                  {result.hindi?.status && (
                    <div className={`p-2.5 rounded-lg text-sm font-medium ${result.is_healthy ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                      {result.hindi.status}
                    </div>
                  )}

                  {/* Language toggle */}
                  <button
                    onClick={() => setShowHindi(!showHindi)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${showHindi
                        ? 'bg-blue-100 text-blue-700 border border-blue-200'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200 border border-gray-200'
                      }`}
                  >
                    <Languages className="w-3.5 h-3.5" />
                    {showHindi ? 'Hide Hindi / हिंदी छिपाएं' : 'Show Hindi / हिंदी दिखाएं'}
                  </button>

                  {/* ── Confidence bar ── */}
                  <ProgressBar
                    label="Model confidence"
                    value={result.confidence}
                    color={result.confidence >= 80 ? 'bg-green-500' : result.confidence >= 60 ? 'bg-yellow-400' : 'bg-red-400'}
                  />

                  <div className="border-t border-gray-100" />

                  {/* ── Symptoms ── */}
                  {result.symptoms?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        Symptoms {showHindi && <span className="normal-case text-blue-400">/ लक्षण</span>}
                      </h5>
                      <SectionList
                        items={result.symptoms}
                        iconClass="bg-amber-400"
                      />
                      {showHindi && result.hindi?.symptoms?.length > 0 && (
                        <ul className="mt-2 space-y-1.5 ml-1">
                          {result.hindi.symptoms.map((s, i) => (
                            <li key={i} className="text-sm text-blue-500 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* ── Treatment ── */}
                  {result.treatment?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-green-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5" /> Treatment plan
                        {showHindi && <span className="normal-case text-blue-400 font-normal">/ उपचार योजना</span>}
                      </h5>
                      <ol className="space-y-2">
                        {result.treatment.map((t, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                            <span className="w-5 h-5 rounded-full bg-green-50 border border-green-200 text-green-700 text-xs font-semibold flex items-center justify-center flex-shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            {t}
                          </li>
                        ))}
                      </ol>
                      {showHindi && result.hindi?.treatment?.length > 0 && (
                        <ol className="mt-2 space-y-1.5 ml-1">
                          {result.hindi.treatment.map((t, i) => (
                            <li key={i} className="text-sm text-blue-500 flex items-start gap-2">
                              <span className="w-5 h-5 rounded-full bg-blue-50 border border-blue-200 text-blue-600 text-xs font-semibold flex items-center justify-center flex-shrink-0 mt-0.5">
                                {i + 1}
                              </span>
                              {t}
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>
                  )}

                  {/* ── Prevention ── */}
                  {result.prevention?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-blue-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5" /> Prevention tips
                        {showHindi && <span className="normal-case text-blue-400 font-normal">/ रोकथाम</span>}
                      </h5>
                      <SectionList
                        items={result.prevention}
                        iconClass="bg-blue-400"
                      />
                      {showHindi && result.hindi?.prevention?.length > 0 && (
                        <ul className="mt-2 space-y-1.5 ml-1">
                          {result.hindi.prevention.map((p, i) => (
                            <li key={i} className="text-sm text-blue-500 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                              {p}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* ── Top-3 predictions (collapsible) ── */}
                  {result.top_predictions?.length > 0 && (
                    <div className="border-t border-gray-100 pt-3">
                      <button
                        onClick={() => setShowTop3(!showTop3)}
                        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        {showTop3 ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        Other possibilities
                      </button>
                      <AnimatePresence>
                        {showTop3 && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-3 space-y-2"
                          >
                            {result.top_predictions.map((p, i) => (
                              <ProgressBar
                                key={i}
                                label={`${p.crop} — ${p.class}`}
                                value={p.confidence}
                                color={i === 0 ? 'bg-green-500' : 'bg-gray-300'}
                              />
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>

      {/* ── Information Section ── */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card-static p-6 mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
          {/* English Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-green-500" /> About Disease Detection
            </h3>
            <div>
              <p className="font-semibold text-green-400">How to use:</p>
              <p>Upload a clear image of the affected plant leaf. Ensure good lighting and focus on the diseased area. Click 'Analyze Plant' to get instant results.</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">Why it is productive:</p>
              <p>Early detection prevents crop loss, reduces unnecessary pesticide use, and helps you apply the correct treatment at the right time.</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">Supported Plants & Diseases:</p>
              <p>Our AI model supports 14 common crops (including Apple, Cherry, Corn, Grape, Peach, Pepper, Potato, Tomato, Strawberry, Squash, Raspberry, Soybean, Blueberry, Orange) and can detect over 38 different plant diseases.</p>
            </div>
          </div>

          {/* Hindi Details */}
          <div className="space-y-4 text-gray-300">
            <h3 className="text-lg font-bold text-green-500 flex items-center gap-2">
              <Languages className="w-5 h-5 text-green-500" /> रोग का पता लगाने के बारे में
            </h3>
            <div>
              <p className="font-semibold text-green-400">उपयोग कैसे करें (How to use):</p>
              <p>प्रभावित पौधे की पत्ती की एक साफ तस्वीर अपलोड करें। सुनिश्चित करें कि रोशनी अच्छी हो और रोगग्रस्त हिस्से पर ध्यान केंद्रित हो। तुरंत परिणाम प्राप्त करने के लिए 'Analyze Plant' पर क्लिक करें।</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">यह कैसे फायदेमंद है (Why it is productive):</p>
              <p>प्रारंभिक पहचान से फसल के नुकसान को रोका जा सकता है, अनावश्यक कीटनाशकों का उपयोग कम होता है, और सही समय पर सही उपचार करने में मदद मिलती है।</p>
            </div>
            <div>
              <p className="font-semibold text-green-400">समर्थित पौधे और रोग (Supported Plants & Diseases):</p>
              <p>हमारा AI मॉडल 14 सामान्य फसलों (सेब, चेरी, मक्का, अंगूर, आड़ू, काली मिर्च, आलू, टमाटर, स्ट्रॉबेरी, स्क्वैश, रास्पबेरी, सोयाबीन, ब्लूबेरी, संतरा) का समर्थन करता है और 38 से अधिक विभिन्न पौधों की बीमारियों का पता लगा सकता है।</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Advisory note ── */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-xs text-center text-gray-400"
      >
        AI diagnosis is advisory only. For severe infections, consult a local agronomist.
      </motion.p>
    </div>
  );
}
