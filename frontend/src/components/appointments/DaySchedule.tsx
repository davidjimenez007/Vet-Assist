'use client';

import { useMemo, useState, useEffect } from 'react';
import Link from 'next/link';
import { Clock, User, PawPrint } from 'lucide-react';

interface Appointment {
  id: string;
  start_time: string;
  end_time?: string;
  duration_minutes: number;
  appointment_type: string;
  reason?: string;
  status: string;
  pet_name?: string;
  pet_type?: string;
  client_name?: string;
  client_phone?: string;
}

interface DayScheduleProps {
  date: string; // YYYY-MM-DD
  appointments: Appointment[];
  startHour?: number;
  endHour?: number;
}

const statusColors: Record<string, string> = {
  scheduled: 'bg-blue-100 border-blue-300 text-blue-800 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300',
  confirmed: 'bg-green-100 border-green-300 text-green-800 dark:bg-green-900/30 dark:border-green-700 dark:text-green-300',
  completed: 'bg-gray-100 border-gray-300 text-gray-600 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400',
  cancelled: 'bg-red-100 border-red-300 text-red-800 dark:bg-red-900/30 dark:border-red-700 dark:text-red-300',
  no_show: 'bg-amber-100 border-amber-300 text-amber-800 dark:bg-amber-900/30 dark:border-amber-700 dark:text-amber-300',
};

const typeLabels: Record<string, string> = {
  consultation: 'Consulta',
  vaccination: 'Vacunación',
  surgery: 'Cirugía',
  emergency: 'Emergencia',
  grooming: 'Peluquería',
  control: 'Control',
};

const petEmojis: Record<string, string> = {
  dog: '🐕',
  cat: '🐈',
  other: '🐾',
};

export default function DaySchedule({
  date,
  appointments,
  startHour = 8,
  endHour = 18,
}: DayScheduleProps) {
  // Track if we're mounted (client-side) to avoid hydration mismatch
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Generate hour slots
  const hours = useMemo(() => {
    const slots = [];
    for (let h = startHour; h <= endHour; h++) {
      slots.push(h);
    }
    return slots;
  }, [startHour, endHour]);

  // Parse appointments and position them with safety checks
  const positionedAppointments = useMemo(() => {
    if (!appointments || !Array.isArray(appointments)) return [];

    return appointments
      .filter((apt) => apt && apt.status !== 'cancelled' && apt.start_time)
      .map((apt) => {
        try {
          const startTime = new Date(apt.start_time);
          if (isNaN(startTime.getTime())) {
            return null; // Invalid date, skip this appointment
          }

          const startHourDecimal = startTime.getHours() + startTime.getMinutes() / 60;
          const duration = apt.duration_minutes || 30;
          const durationHours = duration / 60;

          // Calculate position
          const top = ((startHourDecimal - startHour) / (endHour - startHour + 1)) * 100;
          const height = (durationHours / (endHour - startHour + 1)) * 100;

          return {
            ...apt,
            top: Math.max(0, top),
            height: Math.max(2, Math.min(height, 100 - top)),
            startHourDecimal,
          };
        } catch {
          return null; // Error processing appointment, skip it
        }
      })
      .filter((apt): apt is NonNullable<typeof apt> =>
        apt !== null && apt.startHourDecimal >= startHour && apt.startHourDecimal <= endHour
      );
  }, [appointments, startHour, endHour]);

  // Format time without locale to avoid SSR/CSR mismatch
  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return '--:--';
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const period = hours >= 12 ? 'PM' : 'AM';
      const displayHour = hours > 12 ? hours - 12 : hours === 0 ? 12 : hours;
      return `${displayHour}:${minutes.toString().padStart(2, '0')} ${period}`;
    } catch {
      return '--:--';
    }
  };

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:00 ${period}`;
  };

  const totalHours = endHour - startHour + 1;
  const rowHeight = 60; // pixels per hour

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
        <h3 className="font-medium text-gray-900 dark:text-white">
          {formatDateHeader(date)}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {positionedAppointments.length} citas programadas
        </p>
      </div>

      {/* Schedule Grid */}
      <div className="relative" style={{ height: `${totalHours * rowHeight}px` }}>
        {/* Hour lines */}
        {hours.map((hour, index) => (
          <div
            key={hour}
            className="absolute left-0 right-0 border-t dark:border-gray-700 flex"
            style={{ top: `${index * rowHeight}px`, height: `${rowHeight}px` }}
          >
            <div className="w-20 flex-shrink-0 px-2 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50">
              {formatHour(hour)}
            </div>
            <div className="flex-1 border-l dark:border-gray-700" />
          </div>
        ))}

        {/* Appointments */}
        <div className="absolute left-20 right-2 top-0 bottom-0">
          {positionedAppointments.map((apt) => (
            <Link
              key={apt.id}
              href={`/appointments/${apt.id}`}
              className={`
                absolute left-1 right-1 rounded-lg border-l-4 px-3 py-2 overflow-hidden
                transition-all hover:shadow-md hover:scale-[1.02] cursor-pointer
                ${statusColors[apt.status] || statusColors.scheduled}
              `}
              style={{
                top: `${apt.top}%`,
                height: `${apt.height}%`,
                minHeight: '40px',
              }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3 h-3 flex-shrink-0" />
                    <span className="text-xs font-medium truncate">
                      {formatTime(apt.start_time)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-sm">
                      {petEmojis[apt.pet_type || 'other']}
                    </span>
                    <span className="font-medium text-sm truncate">
                      {apt.pet_name || 'Sin nombre'}
                    </span>
                  </div>
                </div>
                <span className="text-xs bg-white/50 dark:bg-black/20 px-1.5 py-0.5 rounded flex-shrink-0">
                  {typeLabels[apt.appointment_type] || apt.appointment_type}
                </span>
              </div>
              {apt.client_name && apt.height > 8 && (
                <div className="flex items-center gap-1 mt-1 text-xs opacity-75">
                  <User className="w-3 h-3" />
                  <span className="truncate">{apt.client_name}</span>
                </div>
              )}
            </Link>
          ))}
        </div>

        {/* Current time indicator - only render on client to avoid hydration mismatch */}
        {isMounted && isToday(date) && <CurrentTimeIndicator startHour={startHour} endHour={endHour} />}
      </div>

      {/* No appointments message */}
      {positionedAppointments.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-gray-400 dark:text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No hay citas para este día</p>
          </div>
        </div>
      )}
    </div>
  );
}

function CurrentTimeIndicator({
  startHour,
  endHour,
}: {
  startHour: number;
  endHour: number;
}) {
  const now = new Date();
  const currentHour = now.getHours() + now.getMinutes() / 60;

  if (currentHour < startHour || currentHour > endHour) return null;

  const top = ((currentHour - startHour) / (endHour - startHour + 1)) * 100;

  return (
    <div
      className="absolute left-0 right-0 flex items-center z-10 pointer-events-none"
      style={{ top: `${top}%` }}
    >
      <div className="w-20 flex items-center justify-end pr-1">
        <div className="w-2 h-2 rounded-full bg-red-500" />
      </div>
      <div className="flex-1 h-0.5 bg-red-500" />
    </div>
  );
}

function isToday(dateStr: string): boolean {
  try {
    const today = new Date();
    const date = new Date(dateStr + 'T12:00:00');
    return (
      today.getFullYear() === date.getFullYear() &&
      today.getMonth() === date.getMonth() &&
      today.getDate() === date.getDate()
    );
  } catch {
    return false;
  }
}

// Format date header without locale-dependent methods to avoid SSR/CSR mismatch
function formatDateHeader(dateStr: string): string {
  try {
    const date = new Date(dateStr + 'T12:00:00');
    if (isNaN(date.getTime())) return dateStr;

    const weekdays = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

    const weekday = weekdays[date.getDay()];
    const day = date.getDate();
    const month = months[date.getMonth()];

    return `${weekday}, ${day} de ${month}`;
  } catch {
    return dateStr;
  }
}
