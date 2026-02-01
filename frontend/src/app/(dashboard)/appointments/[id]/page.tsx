'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Phone, Clock, Edit, Trash2 } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import EditAppointmentForm from '@/components/appointments/EditAppointmentForm';
import { appointments } from '@/lib/api';
import {
  formatDate,
  formatTime,
  formatPhone,
  getPetEmoji,
  translateStatus,
  getStatusColor,
} from '@/lib/utils';

interface Appointment {
  id: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  appointment_type: string;
  reason?: string;
  status: string;
  source: string;
  notes?: string;
  pet_name?: string;
  pet_species?: string;
  client_name?: string;
  client_phone?: string;
  staff_name?: string;
}

export default function AppointmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditOpen, setIsEditOpen] = useState(false);

  const fetchAppointment = async () => {
    try {
      const data = await appointments.get(params.id as string);
      setAppointment(data);
    } catch (error) {
      console.error('Error fetching appointment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointment();
  }, [params.id]);

  const handleEditSuccess = () => {
    setIsEditOpen(false);
    fetchAppointment();
  };

  const handleCancel = async () => {
    if (!appointment) return;
    if (!confirm('Esta seguro de cancelar esta cita?')) return;

    try {
      await appointments.delete(appointment.id);
      router.push('/appointments');
    } catch (error) {
      console.error('Error cancelling appointment:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
      </div>
    );
  }

  if (!appointment) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          Cita no encontrada
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Detalle de cita
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setIsEditOpen(true)}>
            <Edit className="h-4 w-4 mr-2" />
            Editar
          </Button>
          <Button variant="danger" onClick={handleCancel}>
            <Trash2 className="h-4 w-4 mr-2" />
            Cancelar
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Appointment info */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Informacion de la cita
            </h2>
            <Badge className={getStatusColor(appointment.status)}>
              {translateStatus(appointment.status)}
            </Badge>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-gray-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                  {formatDate(appointment.start_time, "EEEE, d 'de' MMMM 'de' yyyy")}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)} ({appointment.duration_minutes} min)
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Tipo de cita
              </label>
              <p className="text-gray-900 dark:text-gray-100 capitalize">
                {appointment.appointment_type}
              </p>
            </div>

            {appointment.reason && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Motivo
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {appointment.reason}
                </p>
              </div>
            )}

            {appointment.staff_name && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Veterinario
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {appointment.staff_name}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Fuente
              </label>
              <p className="text-gray-900 dark:text-gray-100 capitalize">
                {appointment.source.replace('_', ' ')}
              </p>
            </div>

            {appointment.notes && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Notas
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {appointment.notes}
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Client and pet info */}
        <div className="space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Cliente
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Nombre
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {appointment.client_name || '-'}
                </p>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                    Telefono
                  </label>
                  <p className="text-gray-900 dark:text-gray-100">
                    {formatPhone(appointment.client_phone || '-')}
                  </p>
                </div>
                {appointment.client_phone && (
                  <a
                    href={`tel:${appointment.client_phone}`}
                    className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg text-primary-600 dark:text-primary-400 hover:bg-primary-200 dark:hover:bg-primary-800"
                  >
                    <Phone className="h-5 w-5" />
                  </a>
                )}
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Mascota
            </h2>
            <div className="flex items-center gap-3">
              <span className="text-4xl">
                {getPetEmoji(appointment.pet_species || 'other')}
              </span>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {appointment.pet_name || 'Sin nombre'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {appointment.pet_species}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Edit Appointment Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Editar cita"
        size="lg"
      >
        <EditAppointmentForm
          appointment={appointment}
          onSuccess={handleEditSuccess}
          onCancel={() => setIsEditOpen(false)}
        />
      </Modal>
    </div>
  );
}
