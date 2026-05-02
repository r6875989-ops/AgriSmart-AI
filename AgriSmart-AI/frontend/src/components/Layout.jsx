import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import {
  LayoutDashboard, Scan, Flower2, TrendingUp, Mic,
  ClipboardList, Settings, LogOut, Menu, X, Leaf, Home
} from 'lucide-react';

const sidebarLinks = [
  {
    label: 'OVERVIEW', items: [
      { to: '/', icon: Home, label: 'Home' },
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    ]
  },
  {
    label: 'AI TOOLS', items: [
      { to: '/disease', icon: Scan, label: 'Disease detect' },
      { to: '/fertilizer', icon: Flower2, label: 'Fertilizer' },
      { to: '/price', icon: TrendingUp, label: 'Market prices' },
      { to: '/voice', icon: Mic, label: 'Voice AI' },
    ]
  },
  {
    label: 'ACCOUNT', items: [
      { to: '/dashboard', icon: ClipboardList, label: 'Activity log' },
    ]
  },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-dark">
      {/* Mobile Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-bg-sidebar border-r border-border-dark flex flex-col transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-border-dark">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-semibold">
            <span className="text-secondary">Agri</span>
            <span className="text-accent">Smart</span>
            <span className="text-text-secondary text-sm ml-1">AI</span>
          </span>
          <button
            className="ml-auto lg:hidden text-text-secondary hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {sidebarLinks.map((group) => (
            <div key={group.label} className="mb-6">
              <p className="text-[11px] font-semibold text-text-muted tracking-wider uppercase px-3 mb-2">
                {group.label}
              </p>
              {group.items.map((item) => (
                <NavLink
                  key={item.to + item.label}
                  to={item.to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 mb-1 ${isActive
                      ? 'bg-primary/20 text-secondary border border-primary/30'
                      : 'text-text-secondary hover:text-text-primary hover:bg-bg-card'
                    }`
                  }
                >
                  <item.icon className="w-[18px] h-[18px]" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}

          {/* Sign Out */}
          <div className="mb-4">
            <p className="text-[11px] font-semibold text-text-muted tracking-wider uppercase px-3 mb-2">
            </p>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-danger hover:bg-danger/10 w-full transition-all duration-200"
            >
              <LogOut className="w-[18px] h-[18px]" />
              Sign out
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 border-b border-border-dark flex items-center justify-between px-4 lg:px-8 bg-bg-dark/80 backdrop-blur-md sticky top-0 z-30">
          <button
            className="lg:hidden text-text-secondary hover:text-white p-2"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex-1" />

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-secondary hidden sm:block">
              {user?.name || 'User'}
            </span>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-semibold">
              {getInitials(user?.name)}
            </div>
            <button
              onClick={handleLogout}
              className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg bg-bg-card border border-border-dark text-sm text-text-secondary hover:text-white hover:border-danger transition-all"
            >
              Sign out
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
