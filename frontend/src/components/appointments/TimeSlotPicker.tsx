'use client';

import { useState, useEffect } from 'react';
import { appointments } from '@/lib/api';
import { Clock, Loader2, AlertCircle } from 'lucide-react';

interface TimeSlot {
  start: string;
  end: string;
}

interface TimeSlotPickerProps {
  date: string;
  selectedSlot: string | null;
  onSelectSlot: (slot: string) => void;
  disabled?: boolean;
}

export default function TimeSlotPicker({
  date,
  selectedSlot,
  onSelectSlot,
  disabled = false,
}: TimeSlotPickerProps) {
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!date) {
      setSlots([]);
      return;
    }

    const fetchSlots = async () => {
      setLoading(true);
      setError(null);
      try {
        const availableSlots = await appointments.getAvailableSlots(date);
        setSlots(availableSlots || []);
      } catch (err) {
        console.error('Error fetching slots:', err);
        setError('Error al cargar horarios');
        setSlots([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSlots();
  }, [date]);

  const formatTime = (time: string) => {
    const [hour, minute] = time.split(':').map(Number);
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
  };

  // Group slots by period (morning/afternoon)
  const morningSlots = slots.filter((s) => {
    const hour = parseInt(s.start.split(':')[0]);
    return hour < 12;
  });
  const afternoonSlots = slots.filter((s) => {
    const hour = parseInt(s.start.split(':')[0]);
    return hour >= 12;
  });

  if (!date) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Selecciona una fecha para ver horarios disponibles</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin text-primary-500" />
        <p className="text-sm text-gray-500 dark:text-gray-400">Cargando horarios...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="text-center py-8 text-amber-600 dark:text-amber-400">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="text-sm font-medium">No hay horarios disponibles</p>
        <p className="text-xs mt-1 text-gray-500">Intenta con otra fecha</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {morningSlots.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
            Mañana
          </h4>
          <div className="grid grid-cols-4 gap-2">
            {morningSlots.map((slot) => (
              <button
                key={slot.start}
                type="button"
                disabled={disabled}
                onClick={() => onSelectSlot(slot.start)}
                className={`
                  px-3 py-2 text-sm rounded-lg border transition-all
                  ${
                    selectedSlot === slot.start
                      ? 'bg-primary-500 text-white border-primary-500 ring-2 ring-primary-500/30'
                      : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                {formatTime(slot.start)}
              </button>
            ))}
          </div>
        </div>
      )}

      {afternoonSlots.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
            Tarde
          </h4>
          <div className="grid grid-cols-4 gap-2">
            {afternoonSlots.map((slot) => (
              <button
                key={slot.start}
                type="button"
                disabled={disabled}
                onClick={() => onSelectSlot(slot.start)}
                className={`
                  px-3 py-2 text-sm rounded-lg border transition-all
                  ${
                    selectedSlot === slot.start
                      ? 'bg-primary-500 text-white border-primary-500 ring-2 ring-primary-500/30'
                      : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                {formatTime(slot.start)}
              </button>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
        {slots.length} horarios disponibles
      </p>
    </div>
  );
}
