'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { appointments } from '@/lib/api';

interface Appointment {
  id: string;
  start_time: string;
  end_time: string;
  appointment_type: string;
  reason?: string;
  status: string;
  notes?: string;
}

interface EditAppointmentFormProps {
  appointment: Appointment;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function EditAppointmentForm({
  appointment,
  onSuccess,
  onCancel,
}: EditAppointmentFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Parse existing start_time to date and time
  const existingDate = appointment.start_time.split('T')[0];
  const existingTime = appointment.start_time.split('T')[1]?.substring(0, 5) || '';

  const [formData, setFormData] = useState({
    date: existingDate,
    time: existingTime,
    reason: appointment.reason || '',
    appointment_type: appointment.appointment_type || 'consulta',
    status: appointment.status,
    notes: appointment.notes || '',
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const updateData: Record<string, unknown> = {};

      // Check if date/time changed
      const newStartTime = `${formData.date}T${formData.time}:00`;
      const originalStartTime = `${existingDate}T${existingTime}:00`;
      if (newStartTime !== originalStartTime) {
        updateData.start_time = newStartTime;
      }

      if (formData.reason !== (appointment.reason || '')) {
        updateData.reason = formData.reason || null;
      }

      if (formData.appointment_type !== appointment.appointment_type) {
        updateData.appointment_type = formData.appointment_type;
      }

      if (formData.status !== appointment.status) {
        updateData.status = formData.status;
      }

      if (formData.notes !== (appointment.notes || '')) {
        updateData.notes = formData.notes || null;
      }

      // Only update if something changed
      if (Object.keys(updateData).length === 0) {
        onCancel();
        return;
      }

      await appointments.update(appointment.id, updateData);
      onSuccess();
    } catch (err: unknown) {
      console.error('Error updating appointment:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Error al actualizar la cita');
      } else {
        setError('Error al actualizar la cita');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Fecha
          </label>
          <Input
            type="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Hora
          </label>
          <Input
            type="time"
            name="time"
            value={formData.time}
            onChange={handleChange}
            min="08:00"
            max="18:00"
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Tipo de cita
          </label>
          <select
            name="appointment_type"
            value={formData.appointment_type}
            onChange={handleChange}
            className="input"
          >
            <option value="consulta">Consulta</option>
            <option value="vacunacion">Vacunacion</option>
            <option value="cirugia">Cirugia</option>
            <option value="emergencia">Emergencia</option>
            <option value="control">Control</option>
            <option value="otro">Otro</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Estado
          </label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
            className="input"
          >
            <option value="scheduled">Programada</option>
            <option value="confirmed">Confirmada</option>
            <option value="completed">Completada</option>
            <option value="no_show">No asistio</option>
            <option value="cancelled">Cancelada</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Motivo de la consulta
        </label>
        <textarea
          name="reason"
          value={formData.reason}
          onChange={handleChange}
          placeholder="Motivo de la visita..."
          className="input min-h-[80px]"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Notas
        </label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Notas adicionales..."
          className="input min-h-[80px]"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
        </Button>
      </div>
    </form>
  );
}
