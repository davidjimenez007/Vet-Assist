'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Calendar,
  MessageSquare,
  Settings,
  LogOut,
  Stethoscope,
  Users,
  PawPrint,
  Bot,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth';
import { conversations } from '@/lib/api';

const navigation = [
  { name: 'Panel', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Citas', href: '/appointments', icon: Calendar },
  { name: 'Asistente IA', href: '/chat', icon: Bot },
  { name: 'Clientes', href: '/clients', icon: PawPrint },
  { name: 'Conversaciones', href: '/conversations', icon: MessageSquare, showBadge: true },
  { name: 'Leads', href: '/demo-requests', icon: Users },
  { name: 'Configuracion', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, isAuthenticated } = useAuth();
  const [activeConversations, setActiveConversations] = useState(0);

  const fetchActiveConversations = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await conversations.list({ status: 'active', limit: 50 });
      setActiveConversations(data.length);
    } catch (error) {
      // Silently fail - not critical
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchActiveConversations();
    // Refresh every 15 seconds
    const interval = setInterval(fetchActiveConversations, 15000);
    return () => clearInterval(interval);
  }, [fetchActiveConversations]);

  return (
    <div className="flex flex-col h-full w-64 bg-white dark:bg-dark-surface border-r border-gray-200 dark:border-dark-border">
      {/* Logo */}
      <div className="flex items-center gap-2 h-16 px-6 border-b border-gray-200 dark:border-dark-border">
        <Stethoscope className="h-8 w-8 text-primary-600" />
        <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
          VetAssist
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const showBadge = item.showBadge && activeConversations > 0;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className="h-5 w-5" />
                {item.name}
              </div>
              {showBadge && (
                <span className="flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold text-white bg-green-500 rounded-full animate-pulse">
                  {activeConversations}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-gray-200 dark:border-dark-border">
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
        >
          <LogOut className="h-5 w-5" />
          Cerrar sesion
        </button>
      </div>
    </div>
  );
}
