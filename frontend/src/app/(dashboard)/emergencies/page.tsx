'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Phone, Clock, CheckCircle, XCircle, RefreshCw, ChevronRight } from 'lucide-react';
import { emergencies } from '@/lib/api';

interface Emergency {
  id: string;
  client_phone: string;
  client_name?: string;
  pet_name?: string;
  pet_species?: string;
  description?: string;
  keywords_detected: string[];
  status: string;
  priority: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  alerts_sent: number;
}

export default function EmergenciesPage() {
  const [emergencyList, setEmergencyList] = useState<Emergency[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  const [selectedEmergency, setSelectedEmergency] = useState<Emergency | null>(null);

  const fetchEmergencies = async () => {
    setIsLoading(true);
    try {
      const params: { status?: string; limit: number } = { limit: 50 };
      if (filter) params.status = filter;

      const data = await emergencies.list(params);
      setEmergencyList(data.items || []);
      setActiveCount(data.active_count || 0);
    } catch (error) {
      console.error('Error fetching emergencies:', error);
      setEmergencyList([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmergencies();
  }, [filter]);

  const handleAcknowledge = async (id: string) => {
    try {
      await emergencies.acknowledge(id);
      fetchEmergencies();
    } catch (error) {
      console.error('Error acknowledging emergency:', error);
      alert('Error al confirmar emergencia');
    }
  };

  const handleResolve = async (id: string, wasFalseAlarm: boolean) => {
    const notes = wasFalseAlarm ? '' : prompt('Notas de resolución (opcional):');
    try {
      await emergencies.resolve(id, { notes: notes || undefined, was_false_alarm: wasFalseAlarm });
      fetchEmergencies();
      setSelectedEmergency(null);
    } catch (error) {
      console.error('Error resolving emergency:', error);
      alert('Error al resolver emergencia');
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('es-CO', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '--';
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { bg: string; text: string; label: string }> = {
      active: { bg: 'bg-red-100', text: 'text-red-700', label: 'Activa' },
      acknowledged: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Confirmada' },
      resolved: { bg: 'bg-green-100', text: 'text-green-700', label: 'Resuelta' },
      false_alarm: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Falsa alarma' },
    };
    const c = config[status] || config.active;
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${c.bg} ${c.text}`}>
        {c.label}
      </span>
    );
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-red-500" />
            Emergencias
          </h1>
          {activeCount > 0 && (
            <p className="text-red-600 text-sm mt-1">
              {activeCount} emergencia{activeCount > 1 ? 's' : ''} activa{activeCount > 1 ? 's' : ''}
            </p>
          )}
        </div>
        <button
          onClick={fetchEmergencies}
          className="p-2 border rounded hover:bg-gray-100"
          title="Actualizar"
        >
          <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {[
          { key: null, label: 'Todas' },
          { key: 'active', label: 'Activas' },
          { key: 'acknowledged', label: 'Confirmadas' },
          { key: 'resolved', label: 'Resueltas' },
        ].map((f) => (
          <button
            key={f.key || 'all'}
            onClick={() => setFilter(f.key)}
            className={`px-4 py-2 text-sm rounded-lg ${
              filter === f.key
                ? 'bg-gray-900 text-white'
                : 'bg-white border hover:bg-gray-50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Emergency List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Cargando emergencias...</div>
      ) : emergencyList.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No hay emergencias {filter ? `con estado "${filter}"` : ''}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {emergencyList.map((emergency) => (
            <div
              key={emergency.id}
              className={`border rounded-lg p-4 ${
                emergency.status === 'active'
                  ? 'border-red-300 bg-red-50'
                  : 'bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusBadge(emergency.status)}
                    <span className="text-sm text-gray-500">
                      {formatDate(emergency.created_at)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">{emergency.client_phone}</span>
                    {emergency.client_name && (
                      <span className="text-gray-500">({emergency.client_name})</span>
                    )}
                  </div>

                  {emergency.pet_name && (
                    <p className="text-sm text-gray-600 mb-1">
                      Mascota: {emergency.pet_name}
                      {emergency.pet_species && ` (${emergency.pet_species})`}
                    </p>
                  )}

                  {emergency.description && (
                    <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                      {emergency.description}
                    </p>
                  )}

                  {emergency.keywords_detected.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {emergency.keywords_detected.slice(0, 5).map((kw, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}

                  {emergency.alerts_sent > 0 && (
                    <p className="text-xs text-gray-500">
                      {emergency.alerts_sent} alerta{emergency.alerts_sent > 1 ? 's' : ''} enviada{emergency.alerts_sent > 1 ? 's' : ''}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  {emergency.status === 'active' && (
                    <button
                      onClick={() => handleAcknowledge(emergency.id)}
                      className="px-3 py-1 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600"
                    >
                      Confirmar
                    </button>
                  )}
                  {(emergency.status === 'active' || emergency.status === 'acknowledged') && (
                    <>
                      <button
                        onClick={() => handleResolve(emergency.id, false)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Resolver
                      </button>
                      <button
                        onClick={() => handleResolve(emergency.id, true)}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 text-gray-600"
                      >
                        Falsa alarma
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
