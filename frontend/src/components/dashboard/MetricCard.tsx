'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import Card from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  alert?: boolean;
  href?: string;
  className?: string;
}

export default function MetricCard({
  title,
  value,
  icon,
  trend,
  alert,
  href,
  className,
}: MetricCardProps) {
  const content = (
    <Card
      className={cn(
        'relative transition-all',
        alert && 'border-red-500',
        href && 'hover:shadow-md hover:border-primary-300 dark:hover:border-primary-700 cursor-pointer',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-gray-100">
            {value}
          </p>
          {trend && (
            <p
              className={cn(
                'mt-1 text-sm',
                trend.isPositive
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-600 dark:text-gray-400'
              )}
            >
              {trend.value}
            </p>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              'p-3 rounded-lg',
              alert
                ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400'
                : 'bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400'
            )}
          >
            {icon}
          </div>
        )}
      </div>
      {alert && (
        <div className="absolute top-2 right-2">
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}
    </Card>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}
