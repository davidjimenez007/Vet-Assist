'use client';

import { Bell, User } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { useAuth } from '@/lib/auth';

export default function Header() {
  const { user } = useAuth();

  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {formatDate(new Date(), "EEEE, d 'de' MMMM")}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
        </button>

        {/* User menu */}
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <div className="h-8 w-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
            <User className="h-5 w-5 text-primary-600 dark:text-primary-400" />
          </div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {user?.name || 'Usuario'}
          </span>
        </button>
      </div>
    </header>
  );
}
