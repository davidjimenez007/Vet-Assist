'use client';

import Link from 'next/link';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { formatTime, getPetEmoji, translateStatus, getStatusColor } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface Appointment {
  id: string;
  start_time: string;
  appointment_type: string;
  status: string;
  pet_name?: string;
  pet_species?: string;
  client_name?: string;
  client_phone?: string;
}

interface AppointmentListProps {
  appointments: Appointment[];
  showViewAll?: boolean;
}

export default function AppointmentList({
  appointments,
  showViewAll = true,
}: AppointmentListProps) {
  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Proximas Citas
        </h3>
        {showViewAll && (
          <Link
            href="/appointments"
            className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            Ver todo
          </Link>
        )}
      </div>

      <div className="space-y-3">
        {appointments.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm py-4 text-center">
            No hay citas programadas
          </p>
        ) : (
          appointments.map((apt) => (
            <Link
              key={apt.id}
              href={`/appointments/${apt.id}`}
              className="block p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 min-w-[60px]">
                    {formatTime(apt.start_time)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span>{getPetEmoji(apt.pet_species || 'other')}</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {apt.pet_name || 'Sin nombre'}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">-</span>
                      <span className="text-gray-600 dark:text-gray-300 capitalize">
                        {apt.appointment_type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {apt.client_name || apt.client_phone}
                    </p>
                  </div>
                </div>
                <Badge className={getStatusColor(apt.status)}>
                  {translateStatus(apt.status)}
                </Badge>
              </div>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}
