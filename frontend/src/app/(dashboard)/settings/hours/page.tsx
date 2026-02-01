'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Save } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { settings } from '@/lib/api';

interface WorkingHours {
  [key: string]: { start: string; end: string } | null;
}

const DAYS = [
  { key: 'monday', label: 'Lunes' },
  { key: 'tuesday', label: 'Martes' },
  { key: 'wednesday', label: 'Miercoles' },
  { key: 'thursday', label: 'Jueves' },
  { key: 'friday', label: 'Viernes' },
  { key: 'saturday', label: 'Sabado' },
  { key: 'sunday', label: 'Domingo' },
];

export default function WorkingHoursPage() {
  const router = useRouter();
  const [hours, setHours] = useState<WorkingHours>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchHours = async () => {
      try {
        const data = await settings.getHours();
        setHours(data);
      } catch (error) {
        console.error('Error fetching hours:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHours();
  }, []);

  const toggleDay = (day: string) => {
    setHours((prev) => ({
      ...prev,
      [day]: prev[day] ? null : { start: '08:00', end: '18:00' },
    }));
  };

  const updateTime = (day: string, field: 'start' | 'end', value: string) => {
    setHours((prev) => ({
      ...prev,
      [day]: prev[day] ? { ...prev[day]!, [field]: value } : null,
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await settings.updateHours(hours);
      router.push('/settings');
    } catch (error) {
      console.error('Error saving hours:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
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
            Horarios de atencion
          </h1>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          <Save className="h-4 w-4 mr-2" />
          {isSaving ? 'Guardando...' : 'Guardar'}
        </Button>
      </div>

      {/* Hours form */}
      <Card>
        <div className="space-y-4">
          {DAYS.map((day) => (
            <div
              key={day.key}
              className="flex items-center gap-4 py-3 border-b border-gray-100 dark:border-gray-800 last:border-0"
            >
              <div className="w-32">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hours[day.key] !== null}
                    onChange={() => toggleDay(day.key)}
                    className="w-4 h-4 text-primary-600 rounded"
                  />
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {day.label}
                  </span>
                </label>
              </div>

              {hours[day.key] ? (
                <div className="flex items-center gap-2">
                  <input
                    type="time"
                    value={hours[day.key]?.start || ''}
                    onChange={(e) => updateTime(day.key, 'start', e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-dark-surface"
                  />
                  <span className="text-gray-500">a</span>
                  <input
                    type="time"
                    value={hours[day.key]?.end || ''}
                    onChange={(e) => updateTime(day.key, 'end', e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-dark-surface"
                  />
                </div>
              ) : (
                <span className="text-gray-500 dark:text-gray-400">Cerrado</span>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
