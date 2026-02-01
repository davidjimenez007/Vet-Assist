'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, RefreshCw, Trash2 } from 'lucide-react';
import NewAppointmentForm from '@/components/appointments/NewAppointmentForm';
import { appointments } from '@/lib/api';

interface Appointment {
  id: string;
  start_time: string;
  duration_minutes: number;
  status: string;
  reason?: string;
  pet_name?: string;
  pet_species?: string;
  client_name?: string;
  client_phone?: string;
}

export default function AppointmentsPage() {
  const [appointmentList, setAppointmentList] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAppointments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await appointments.list({ limit: 50 });
      const validData = Array.isArray(data) ? data : [];
      // Sort by date descending
      validData.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());
      setAppointmentList(validData);
    } catch (err) {
      console.error('Error fetching appointments:', err);
      setError('Error al cargar las citas');
      setAppointmentList([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('¿Cancelar esta cita?')) return;
    try {
      await appointments.delete(id);
      fetchAppointments();
    } catch (err) {
      console.error('Error deleting appointment:', err);
      alert('Error al cancelar la cita');
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-CO', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return 'Fecha inválida';
    }
  };

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleTimeString('es-CO', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '--:--';
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-800',
      confirmed: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    const labels: Record<string, string> = {
      scheduled: 'Programada',
      confirmed: 'Confirmada',
      completed: 'Completada',
      cancelled: 'Cancelada',
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || styles.scheduled}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Citas</h1>
        <div className="flex gap-2">
          <button
            onClick={fetchAppointments}
            className="p-2 border rounded hover:bg-gray-100"
            title="Actualizar"
          >
            <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Plus className="h-5 w-5" />
            Nueva Cita
          </button>
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Nueva Cita</h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <NewAppointmentForm
                onSuccess={() => {
                  setShowForm(false);
                  fetchAppointments();
                }}
                onCancel={() => setShowForm(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-300 rounded text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">
          Cargando citas...
        </div>
      ) : appointmentList.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No hay citas</p>
          <p className="text-sm">Haz clic en "Nueva Cita" para agendar una</p>
        </div>
      ) : (
        /* Appointments List */
        <div className="space-y-3">
          {appointmentList.map((apt) => (
            <div
              key={apt.id}
              className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${
                apt.status === 'cancelled' ? 'opacity-50' : ''
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-medium">
                      {formatDate(apt.start_time)} - {formatTime(apt.start_time)}
                    </span>
                    {getStatusBadge(apt.status)}
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    {apt.pet_name && (
                      <p>
                        🐾 <strong>{apt.pet_name}</strong>
                        {apt.pet_species && ` (${apt.pet_species})`}
                      </p>
                    )}
                    {apt.client_name && <p>👤 {apt.client_name}</p>}
                    {apt.client_phone && <p>📞 {apt.client_phone}</p>}
                    {apt.reason && <p>📋 {apt.reason}</p>}
                  </div>
                </div>

                {apt.status !== 'cancelled' && apt.status !== 'completed' && (
                  <button
                    onClick={() => handleDelete(apt.id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded"
                    title="Cancelar cita"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
