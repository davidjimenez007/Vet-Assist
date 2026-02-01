'use client';

import { useEffect, useState } from 'react';
import { Calendar, Clock, AlertCircle, CheckCircle, XCircle, PawPrint, MessageCircle, RefreshCw } from 'lucide-react';
import { clientApi } from '@/lib/clientApi';
import { useClientAuth } from '@/lib/clientAuth';

interface Appointment {
  id: string;
  pet_name: string | null;
  pet_species: string | null;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
  status: string;
  notes: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
  scheduled: { label: 'Programada', color: 'blue', icon: Calendar },
  confirmed: { label: 'Confirmada', color: 'green', icon: CheckCircle },
  completed: { label: 'Completada', color: 'gray', icon: CheckCircle },
  cancelled: { label: 'Cancelada', color: 'red', icon: XCircle },
  no_show: { label: 'No asistio', color: 'yellow', icon: AlertCircle },
};

const SPECIES_ICONS: Record<string, string> = {
  dog: 'perro',
  cat: 'gato',
  bird: 'ave',
  other: 'otro',
};

export default function ClienteCitasPage() {
  const { client } = useClientAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'upcoming' | 'past' | 'all'>('upcoming');

  useEffect(() => {
    loadAppointments();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadAppointments();
    setIsRefreshing(false);
  };

  const loadAppointments = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await clientApi.getAppointments();
      // Ensure data is valid and filter out appointments without scheduled_at
      const validData = Array.isArray(data) ? data.filter(apt => apt && apt.id && apt.scheduled_at) : [];
      setAppointments(validData);
    } catch (err) {
      console.error('Error loading appointments:', err);
      setError('Error al cargar las citas');
      setAppointments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return 'Fecha no disponible';
      const weekdays = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
      const months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
      return `${weekdays[date.getDay()]}, ${date.getDate()} de ${months[date.getMonth()]}`;
    } catch {
      return 'Fecha no disponible';
    }
  };

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return '--:--';
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const period = hours >= 12 ? 'p.m.' : 'a.m.';
      const displayHour = hours > 12 ? hours - 12 : hours === 0 ? 12 : hours;
      return `${displayHour}:${minutes.toString().padStart(2, '0')} ${period}`;
    } catch {
      return '--:--';
    }
  };

  const isUpcoming = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return false;
      return date > new Date();
    } catch {
      return false;
    }
  };

  const filteredAppointments = appointments.filter((apt) => {
    if (filter === 'upcoming') {
      return isUpcoming(apt.scheduled_at) && apt.status !== 'cancelled';
    }
    if (filter === 'past') {
      return !isUpcoming(apt.scheduled_at) || apt.status === 'cancelled' || apt.status === 'completed';
    }
    return true;
  });

  const upcomingCount = appointments.filter(
    (apt) => isUpcoming(apt.scheduled_at) && apt.status !== 'cancelled'
  ).length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600 dark:text-gray-400">Cargando citas...</div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          Mis Citas
        </h1>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="Actualizar"
        >
          <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        {upcomingCount > 0
          ? `Tienes ${upcomingCount} cita${upcomingCount > 1 ? 's' : ''} proxima${upcomingCount > 1 ? 's' : ''}`
          : 'No tienes citas programadas'}
      </p>

      {/* WhatsApp Banner */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
            <MessageCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <p className="font-medium text-green-800 dark:text-green-200 text-sm">
              Agenda por WhatsApp
            </p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">
              Escribe al WhatsApp de {client?.clinic_name || 'la clinica'} para agendar, cambiar o cancelar citas. El asistente te atendera 24/7.
            </p>
          </div>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'upcoming', label: 'Proximas' },
          { key: 'past', label: 'Pasadas' },
          { key: 'all', label: 'Todas' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key as typeof filter)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              filter === tab.key
                ? 'bg-primary-600 text-white'
                : 'bg-white dark:bg-dark-surface text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm mb-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {filteredAppointments.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="h-12 w-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {filter === 'upcoming'
              ? 'No tienes citas proximas'
              : filter === 'past'
              ? 'No tienes citas pasadas'
              : 'No tienes citas'}
          </p>
          {filter === 'upcoming' && (
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
              Usa el chat para agendar una nueva cita
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAppointments.map((apt) => {
            const statusConfig = STATUS_CONFIG[apt.status] || STATUS_CONFIG.scheduled;
            const StatusIcon = statusConfig.icon;
            const upcoming = isUpcoming(apt.scheduled_at);

            return (
              <div
                key={apt.id}
                className={`bg-white dark:bg-dark-surface border rounded-xl p-4 ${
                  upcoming && apt.status !== 'cancelled'
                    ? 'border-primary-200 dark:border-primary-800'
                    : 'border-gray-200 dark:border-dark-border'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Date and time */}
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
                      <Calendar className="h-4 w-4" />
                      <span className="capitalize">{formatDate(apt.scheduled_at)}</span>
                      <span className="mx-1">-</span>
                      <Clock className="h-4 w-4" />
                      <span>{formatTime(apt.scheduled_at)}</span>
                    </div>

                    {/* Pet info */}
                    {(apt.pet_name || apt.pet_species) && (
                      <div className="flex items-center gap-2 mb-2">
                        <PawPrint className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {apt.pet_name || 'Sin nombre'}
                        </span>
                        {apt.pet_species && (
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            ({SPECIES_ICONS[apt.pet_species] || apt.pet_species})
                          </span>
                        )}
                      </div>
                    )}

                    {/* Reason */}
                    {apt.reason && (
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {apt.reason}
                      </p>
                    )}

                    {/* Duration */}
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                      Duracion: {apt.duration_minutes} min
                    </p>
                  </div>

                  {/* Status badge */}
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                      statusConfig.color === 'blue'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        : statusConfig.color === 'green'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : statusConfig.color === 'red'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : statusConfig.color === 'yellow'
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                    }`}
                  >
                    <StatusIcon className="h-3.5 w-3.5" />
                    {statusConfig.label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
