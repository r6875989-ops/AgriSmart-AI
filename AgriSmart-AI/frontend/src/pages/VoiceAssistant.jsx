import { useState, useEffect, useRef } from 'react';
import { voiceAPI } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, Loader2, Languages, MessageSquare, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

export default function VoiceAssistant() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('hi');
  const [history, setHistory] = useState([]);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      setTranscript(finalTranscript || interimTranscript);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      console.error('Speech error:', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        toast.error('Microphone access denied. Please allow microphone in browser settings.');
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [language]);

  const toggleListening = () => {
    if (!supported) {
      toast.error('Speech recognition not supported in this browser. Use Chrome.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      if (transcript) {
        processVoice(transcript);
      }
    } else {
      setTranscript('');
      setResponse(null);
      try {
        recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        toast.error('Could not start listening');
      }
    }
  };

  const processVoice = async (text) => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await voiceAPI.process(text, language);
      setResponse(res.data);

      // Add to session history
      setHistory(prev => [{
        transcript: text,
        response: res.data,
        timestamp: new Date().toLocaleTimeString('en-IN'),
      }, ...prev]);

      // Speak response
      speakResponse(language === 'hi' ? res.data.response_hindi : res.data.response_text);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to process voice');
    } finally {
      setLoading(false);
    }
  };

  const speakResponse = (text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (transcript.trim()) {
      processVoice(transcript);
    }
  };

  const intentLabels = {
    disease_detection: { label: 'Disease Detection', color: 'badge-warning' },
    fertilizer_recommendation: { label: 'Fertilizer', color: 'badge-success' },
    price_query: { label: 'Price Query', color: 'badge-info' },
    general_farming_query: { label: 'General', color: 'badge-info' },
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-light/10 flex items-center justify-center">
            <Mic className="w-5 h-5 text-primary-light" />
          </div>
          Voice AI Assistant
        </h1>
        <p className="text-text-secondary text-sm mt-2 hindi">
          हिंदी में बोलें या टाइप करें — Ask about diseases, fertilizers, or market prices
        </p>
      </motion.div>

      {/* Language Toggle */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex items-center gap-3">
        <Languages className="w-4 h-4 text-text-muted" />
        <div className="flex rounded-lg bg-bg-card border border-border-dark overflow-hidden">
          <button
            onClick={() => setLanguage('hi')}
            className={`px-4 py-2 text-sm font-medium transition-all ${language === 'hi' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text-primary'}`}
          >
            हिंदी
          </button>
          <button
            onClick={() => setLanguage('en')}
            className={`px-4 py-2 text-sm font-medium transition-all ${language === 'en' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text-primary'}`}
          >
            English
          </button>
        </div>
      </motion.div>

      {/* Main Voice Area */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <div className="glass-card-static p-8 flex flex-col items-center">
          {/* Mic Button */}
          <div className="relative mb-6">
            {isListening && (
              <div className="absolute inset-0 rounded-full animate-pulse-green" style={{ margin: '-15px' }}></div>
            )}
            <button
              onClick={toggleListening}
              disabled={loading}
              className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${isListening
                  ? 'bg-danger text-white shadow-lg shadow-danger/30 scale-110'
                  : 'bg-gradient-to-br from-primary to-secondary text-white hover:shadow-lg hover:shadow-primary/30 hover:scale-105'
                }`}
              id="voice-mic-btn"
            >
              {loading ? (
                <Loader2 className="w-10 h-10 animate-spin" />
              ) : isListening ? (
                <MicOff className="w-10 h-10" />
              ) : (
                <Mic className="w-10 h-10" />
              )}
            </button>
          </div>

          <p className="text-sm text-text-muted mb-4">
            {isListening ? (
              <span className="text-danger font-medium">🎙️ Listening... Click to stop</span>
            ) : loading ? (
              <span className="text-accent">Processing your query...</span>
            ) : (
              <span>{language === 'hi' ? 'माइक बटन दबाएं और बोलें' : 'Click the mic button and speak'}</span>
            )}
          </p>

          {/* Waveform animation */}
          {isListening && (
            <div className="flex items-center gap-1 mb-4 h-8">
              {[...Array(20)].map((_, i) => (
                <motion.div
                  key={i}
                  className="w-1 bg-secondary rounded-full"
                  animate={{ height: [4, Math.random() * 28 + 4, 4] }}
                  transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.05 }}
                />
              ))}
            </div>
          )}

          {/* Text Input Fallback */}
          <form onSubmit={handleTextSubmit} className="w-full max-w-lg flex gap-2 mt-2">
            <input
              type="text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder={language === 'hi' ? 'या यहाँ टाइप करें...' : 'Or type your question here...'}
              className="form-input flex-1 hindi"
              id="voice-text-input"
            />
            <button type="submit" disabled={loading || !transcript.trim()} className="btn-primary">
              Send
            </button>
          </form>
        </div>
      </motion.div>

      {/* Response */}
      {(response || loading) && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="glass-card-static p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> AI Response
            </h3>

            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => <div key={i} className="skeleton-loader h-5 w-full"></div>)}
              </div>
            ) : response && response.error ? (
              <div className="p-4 rounded-xl border border-danger/30 text-center">
                <p className="text-danger font-medium mb-1">Voice Processing Failed</p>
                <p className="text-sm text-text-secondary">{response.error}</p>
                <p className="text-xs text-text-muted mt-2">Please check your NVIDIA API Key in the backend/.env file.</p>
              </div>
            ) : response ? (
              <div className="space-y-4">
                {/* Intent Badge */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-muted">Intent:</span>
                  <span className={`badge text-[11px] ${intentLabels[response.intent]?.color || 'badge-info'}`}>
                    {intentLabels[response.intent]?.label || response.intent}
                  </span>
                  {response.crop && (
                    <span className="badge badge-success text-[11px]">Crop: {response.crop}</span>
                  )}
                </div>

                {/* Hindi Response */}
                {response.response_hindi && (
                  <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                    <p className="text-sm text-text-primary hindi leading-relaxed">{response.response_hindi}</p>
                    <button
                      onClick={() => speakResponse(response.response_hindi)}
                      className="flex items-center gap-1 text-xs text-secondary mt-3 hover:underline"
                    >
                      <Volume2 className="w-3.5 h-3.5" /> सुनें
                    </button>
                  </div>
                )}

                {/* English Response */}
                {response.response_text && (
                  <div className="p-4 rounded-xl bg-bg-card border border-border-dark">
                    <p className="text-sm text-text-secondary leading-relaxed">{response.response_text}</p>
                    <button
                      onClick={() => speakResponse(response.response_text)}
                      className="flex items-center gap-1 text-xs text-secondary mt-3 hover:underline"
                    >
                      <Volume2 className="w-3.5 h-3.5" /> Listen
                    </button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </motion.div>
      )}

      {/* Session History */}
      {history.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="glass-card-static p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4" /> Session History
            </h3>
            <div className="space-y-3">
              {history.map((item, i) => (
                <div key={i} className="p-3 rounded-lg bg-bg-card border border-border-dark">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm text-text-primary hindi">"{item.transcript}"</p>
                      <p className="text-xs text-text-muted mt-1">
                        → {item.response?.query_summary || item.response?.intent}
                      </p>
                    </div>
                    <span className="text-xs text-text-muted flex-shrink-0">{item.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Browser Support Warning */}
      {!supported && (
        <div className="p-4 rounded-xl bg-warning/10 border border-warning/20 text-center">
          <p className="text-sm text-warning">⚠️ Speech recognition is not supported in this browser.</p>
          <p className="text-xs text-text-muted mt-1">Please use Google Chrome or Microsoft Edge for voice features. You can still type your queries above.</p>
        </div>
      )}
    </div>
  );
}
