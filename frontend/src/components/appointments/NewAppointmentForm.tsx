'use client';

import { useState } from 'react';
import { appointments } from '@/lib/api';

interface NewAppointmentFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

// Generate time options from 8:00 to 18:00
const TIME_OPTIONS = [
  '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
  '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30',
  '17:00', '17:30', '18:00'
];

export default function NewAppointmentForm({
  onSuccess,
  onCancel,
}: NewAppointmentFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    client_phone: '',
    client_name: '',
    pet_name: '',
    pet_type: 'dog',
    reason: '',
    date: '',
    time: '',
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!formData.client_phone) {
      setError('El teléfono es requerido');
      return;
    }
    if (!formData.date) {
      setError('La fecha es requerida');
      return;
    }
    if (!formData.time) {
      setError('La hora es requerida');
      return;
    }
    if (!formData.reason) {
      setError('El motivo es requerido');
      return;
    }

    setIsSubmitting(true);

    try {
      // Format phone with +57 prefix
      const phone = formData.client_phone.replace(/\D/g, '');
      const fullPhone = phone.startsWith('57') ? `+${phone}` : `+57${phone}`;

      // Create ISO date string
      const startTimeStr = `${formData.date}T${formData.time}:00`;

      await appointments.create({
        client_phone: fullPhone,
        client_name: formData.client_name || undefined,
        pet_name: formData.pet_name || undefined,
        pet_type: formData.pet_type,
        reason: formData.reason,
        start_time: startTimeStr,
        source: 'manual',
      });

      setSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err: unknown) {
      console.error('Error creating appointment:', err);
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError?.response?.data?.detail || 'Error al crear la cita. Intenta de nuevo.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="p-6 text-center">
        <div className="text-4xl mb-4">✅</div>
        <h3 className="text-lg font-semibold text-green-600">Cita creada exitosamente</h3>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Phone */}
      <div>
        <label className="block text-sm font-medium mb-1">Teléfono *</label>
        <input
          type="tel"
          name="client_phone"
          value={formData.client_phone}
          onChange={handleChange}
          placeholder="3001234567"
          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      {/* Client Name */}
      <div>
        <label className="block text-sm font-medium mb-1">Nombre del cliente</label>
        <input
          type="text"
          name="client_name"
          value={formData.client_name}
          onChange={handleChange}
          placeholder="Juan Pérez"
          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Pet Name and Type */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Mascota</label>
          <input
            type="text"
            name="pet_name"
            value={formData.pet_name}
            onChange={handleChange}
            placeholder="Max"
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Tipo</label>
          <select
            name="pet_type"
            value={formData.pet_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="dog">Perro</option>
            <option value="cat">Gato</option>
            <option value="other">Otro</option>
          </select>
        </div>
      </div>

      {/* Reason */}
      <div>
        <label className="block text-sm font-medium mb-1">Motivo de la consulta *</label>
        <textarea
          name="reason"
          value={formData.reason}
          onChange={handleChange}
          placeholder="Vacunación, consulta general, etc."
          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[60px]"
          required
        />
      </div>

      {/* Date and Time - Simple selects */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Fecha *</label>
          <input
            type="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Hora *</label>
          <select
            name="time"
            value={formData.time}
            onChange={handleChange}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Seleccionar hora</option>
            {TIME_OPTIONS.map((time) => (
              <option key={time} value={time}>
                {time}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t mt-6">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded hover:bg-gray-100"
          disabled={isSubmitting}
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Creando...' : 'Crear Cita'}
        </button>
      </div>
    </form>
  );
}
