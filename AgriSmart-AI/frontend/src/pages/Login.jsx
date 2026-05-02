import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Leaf, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back! 🌾');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-dark flex items-center justify-center p-4">
      {/* Background pattern */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/5 rounded-full blur-3xl"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Leaf className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">
              <span className="text-secondary">Agri</span>
              <span className="text-accent">Smart</span>
              <span className="text-text-secondary text-lg ml-1">AI</span>
            </h1>
            <p className="text-xs text-text-muted">Intelligent Farming Assistant</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass-card-static p-8">
          <h2 className="text-xl font-semibold text-text-primary mb-1">Welcome back</h2>
          <p className="text-text-secondary text-sm mb-6">Sign in to your AgriSmart account</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-text-secondary mb-1.5 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="      demo@agrismart.in"
                  className="form-input pl-10"
                  id="login-email"
                />
              </div>
            </div>

            <div>
              <label className="text-sm text-text-secondary mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="      Enter password"
                  className="form-input pl-10 pr-10"
                  id="login-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
              id="login-submit"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="text-center text-sm text-text-secondary mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-secondary hover:text-secondary-light font-medium">
              Register
            </Link>
          </p>

          {/* Demo credentials */}
          <div className="mt-4 p-3 rounded-lg bg-bg-input border border-border-dark">
            <p className="text-xs text-text-muted text-center">
              Demo: <span className="text-accent">demo@agrismart.in</span> / <span className="text-accent">kisan123</span>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
