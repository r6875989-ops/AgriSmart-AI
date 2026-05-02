import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Scan, Flower2, TrendingUp, Mic, ArrowRight, Leaf, Shield, Zap, Users } from 'lucide-react';

const features = [
  {
    icon: Scan,
    title: 'Disease Detection',
    titleHi: 'रोग पहचान',
    desc: 'Upload crop leaf photos to instantly detect diseases with AI-powered analysis',
    bgColor: 'bg-green-500/20',
    link: '/disease',
  },
  {
    icon: Flower2,
    title: 'Fertilizer Advice',
    titleHi: 'उर्वरक सलाह',
    desc: 'Get personalized fertilizer recommendations based on your soil and crop type',
    bgColor: 'bg-yellow-500/20',
    link: '/fertilizer',
  },
  {
    icon: TrendingUp,
    title: 'Market Prices',
    titleHi: 'बाज़ार भाव',
    desc: 'Predict crop prices with AI and find the best time to sell your produce',
    bgColor: 'bg-blue-500/20',
    link: '/price',
  },
  {
    icon: Mic,
    title: 'Voice Assistant',
    titleHi: 'वॉइस सहायक',
    desc: 'Speak in Hindi to get instant farming answers — no typing needed',
    bgColor: 'bg-purple-500/20',
    link: '/voice',
  },
];

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
};

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen flex flex-col items-center relative overflow-hidden">

      {/* 🌾 Background Image */}
      <div className="absolute inset-0 -z-10">
        <img
          src="https://videocdn.cdnpk.net/videos/abc73900-1852-5ce3-8559-7a6ee5683463/horizontal/thumbnails/large.jpg"
          className="w-full h-full object-cover opacity-20"
          alt="farmer"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-green-900/70 via-black/70 to-black"></div>
      </div>

      {/* Navbar */}
      <nav className="w-full border-b border-border-dark bg-black/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-green-600 flex items-center justify-center animate-pulse">
              <Leaf className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-white">
              AgriSmart AI
            </span>
          </div>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-primary text-sm">
                Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn-secondary text-sm">Sign In</Link>
                <Link to="/register" className="btn-primary text-sm">Get Started</Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="w-full flex justify-center">
        <div className="max-w-7xl w-full px-4 sm:px-6 lg:px-8 pt-20 pb-24 flex justify-center">

          <motion.div
            {...fadeInUp}
            transition={{ duration: 0.6 }}
            className="text-center max-w-3xl mx-auto flex flex-col items-center"
          >

            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-500/20 border border-green-400/30 text-green-300 mb-8 animate-pulse">
              <Zap className="w-3.5 h-3.5" /> AI-Powered Farming Solution
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight text-center">
              Smart Farming with{' '}
              <span className="bg-gradient-to-r from-green-400 to-lime-300 bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h1>

            <p className="text-lg text-gray-300 mt-6 max-w-2xl mx-auto leading-relaxed text-center">
              Detect crop diseases, get fertilizer recommendations, predict market prices, and talk to AI in Hindi — all in one platform built for Indian farmers.
            </p>

            <p className="text-base text-green-300 mt-3 hindi text-center">
              🌾 भारतीय किसानों के लिए AI सहायक
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10 w-full">
              <Link to={isAuthenticated ? '/dashboard' : '/register'} className="btn-primary text-base px-8 py-3.5">
                {isAuthenticated ? 'Go to Dashboard' : 'Start '} <ArrowRight className="w-5 h-5" />
              </Link>
              <Link to="/login" className="btn-secondary text-base px-8 py-3.5">
                Login
              </Link>
            </div>

          </motion.div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="w-full py-20 flex justify-center">
        <div className="max-w-7xl w-full px-4 sm:px-6 lg:px-8">

          <motion.div {...fadeInUp} transition={{ delay: 0.2 }} className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white">Everything a Farmer Needs</h2>
            <p className="text-gray-300 mt-3">Powerful AI tools designed for Indian agriculture</p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 place-items-center">
            {features.map((feature, i) => (
              <motion.div key={i} {...fadeInUp} transition={{ delay: 0.3 + i * 0.1 }}>

                <Link to={isAuthenticated ? feature.link : '/login'}>
                  <div className="glass-card p-6 h-full text-center flex flex-col items-center cursor-pointer backdrop-blur-md bg-white/10 hover:bg-white/20 transition hover:scale-105">

                    <div className={`w-12 h-12 rounded-xl ${feature.bgColor} flex items-center justify-center mb-4`}>
                      <feature.icon className="w-6 h-6 text-green-300" />
                    </div>

                    <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
                    <p className="text-sm text-green-300 hindi mt-0.5">{feature.titleHi}</p>
                    <p className="text-sm text-gray-300 mt-3">{feature.desc}</p>

                    <div className="mt-4 text-green-300 text-sm font-medium flex items-center gap-1 justify-center">
                      Try now <ArrowRight className="w-4 h-4" />
                    </div>

                  </div>
                </Link>

              </motion.div>
            ))}
          </div>

        </div>
      </section>

      {/* FOOTER */}
      <footer className="w-full border-t border-white/10 py-8 text-center">
        <p className="text-gray-400 text-sm">
          AgriSmart AI — Built for Indian Farmers 🌾By :- Rajesh Prajapati 🌾
        </p>
      </footer>

    </div>
  );
}
