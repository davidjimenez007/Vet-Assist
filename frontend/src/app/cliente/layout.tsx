'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { MessageCircle, Calendar, LogOut } from 'lucide-react';
import { useClientAuth } from '@/lib/clientAuth';

export default function ClienteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, checkAuth, logout, client } = useClientAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // Skip auth check for login page
    if (pathname === '/cliente/login') return;

    if (!isLoading && !isAuthenticated) {
      const clinicId = localStorage.getItem('client_clinic_id');
      if (clinicId) {
        router.push(`/cliente/login?clinic=${clinicId}`);
      } else {
        router.push('/cliente/login');
      }
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  // Don't show layout for login page
  if (pathname === '/cliente/login') {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleLogout = () => {
    logout();
    const clinicId = localStorage.getItem('client_clinic_id');
    if (clinicId) {
      router.push(`/cliente/login?clinic=${clinicId}`);
    } else {
      router.push('/cliente/login');
    }
  };

  const navItems = [
    { href: '/cliente/citas', icon: Calendar, label: 'Mis Citas' },
    { href: '/cliente/chat', icon: MessageCircle, label: 'Ayuda' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">V</span>
          </div>
          <div>
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {client?.clinic_name || 'VetAssist'}
            </span>
            {client?.name && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Hola, {client.name}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          title="Cerrar sesion"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* Bottom navigation */}
      <nav className="bg-white dark:bg-dark-surface border-t border-gray-200 dark:border-dark-border px-4 py-2 safe-area-bottom">
        <div className="flex items-center justify-around max-w-md mx-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                <item.icon className={`h-6 w-6 ${isActive ? 'stroke-2' : ''}`} />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
