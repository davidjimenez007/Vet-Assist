'use client';

import { useEffect, useState } from 'react';
import { Mail, Phone, Building2, Clock, MessageSquare } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { demoRequests } from '@/lib/api';

interface DemoRequest {
  id: string;
  clinic_name: string;
  contact_name: string;
  email: string;
  phone: string;
  clinic_size: string | null;
  preferred_time: string | null;
  message: string | null;
  status: string;
  created_at: string;
}

const statusLabels: Record<string, string> = {
  pending: 'Pendiente',
  contacted: 'Contactado',
  converted: 'Convertido',
  dismissed: 'Descartado',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  contacted: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  converted: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  dismissed: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

const clinicSizeLabels: Record<string, string> = {
  '1-2': '1-2 veterinarios',
  '3-5': '3-5 veterinarios',
  '6-10': '6-10 veterinarios',
  '10+': 'Mas de 10',
};

const preferredTimeLabels: Record<string, string> = {
  morning: 'Manana',
  afternoon: 'Tarde',
  anytime: 'Cualquier hora',
};

export default function DemoRequestsPage() {
  const [requests, setRequests] = useState<DemoRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchRequests = async () => {
    setIsLoading(true);
    try {
      const params: { status?: string } = {};
      if (filterStatus) params.status = filterStatus;
      const data = await demoRequests.list(params);
      setRequests(data);
    } catch (error) {
      console.error('Error fetching demo requests:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [filterStatus]);

  const handleStatusChange = async (id: string, newStatus: string) => {
    setUpdatingId(id);
    try {
      await demoRequests.updateStatus(id, newStatus);
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: newStatus } : r))
      );
    } catch (error) {
      console.error('Error updating status:', error);
    } finally {
      setUpdatingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const pendingCount = requests.filter((r) => r.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Solicitudes de Demo
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {pendingCount > 0
              ? `${pendingCount} solicitud${pendingCount > 1 ? 'es' : ''} pendiente${pendingCount > 1 ? 's' : ''}`
              : 'No hay solicitudes pendientes'}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['', 'pending', 'contacted', 'converted', 'dismissed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filterStatus === status
                ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
            }`}
          >
            {status === '' ? 'Todos' : statusLabels[status]}
          </button>
        ))}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
        </div>
      ) : requests.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No hay solicitudes de demo
            {filterStatus ? ` con estado "${statusLabels[filterStatus]}"` : ''}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <Card key={req.id} className="overflow-hidden">
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                onClick={() =>
                  setExpandedId(expandedId === req.id ? null : req.id)
                }
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {req.clinic_name}
                      </h3>
                      <Badge className={statusColors[req.status] || ''}>
                        {statusLabels[req.status] || req.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        <Building2 className="h-4 w-4" />
                        {req.contact_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <Mail className="h-4 w-4" />
                        {req.email}
                      </span>
                      <span className="flex items-center gap-1">
                        <Phone className="h-4 w-4" />
                        {req.phone}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap ml-4">
                    {formatDate(req.created_at)}
                  </span>
                </div>
              </div>

              {/* Expanded details */}
              {expandedId === req.id && (
                <div className="border-t border-gray-200 dark:border-dark-border p-4 bg-gray-50 dark:bg-gray-800/30 space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {req.clinic_size && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">
                          Tamano de clinica:
                        </span>
                        <span className="ml-2 text-gray-900 dark:text-gray-100">
                          {clinicSizeLabels[req.clinic_size] || req.clinic_size}
                        </span>
                      </div>
                    )}
                    {req.preferred_time && (
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-500 dark:text-gray-400">
                          Horario preferido:
                        </span>
                        <span className="ml-1 text-gray-900 dark:text-gray-100">
                          {preferredTimeLabels[req.preferred_time] || req.preferred_time}
                        </span>
                      </div>
                    )}
                  </div>

                  {req.message && (
                    <div className="text-sm">
                      <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400 mb-1">
                        <MessageSquare className="h-4 w-4" />
                        Mensaje:
                      </div>
                      <p className="text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                        {req.message}
                      </p>
                    </div>
                  )}

                  {/* Status actions */}
                  <div className="flex items-center gap-2 pt-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">
                      Cambiar estado:
                    </span>
                    {['pending', 'contacted', 'converted', 'dismissed'].map(
                      (status) => (
                        <button
                          key={status}
                          disabled={
                            req.status === status || updatingId === req.id
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStatusChange(req.id, status);
                          }}
                          className={`px-3 py-1 rounded text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                            req.status === status
                              ? statusColors[status]
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                          }`}
                        >
                          {statusLabels[status]}
                        </button>
                      )
                    )}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
