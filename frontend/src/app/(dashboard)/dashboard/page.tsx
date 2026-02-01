'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Calendar, MessageCircle, Bot, Users, RefreshCw } from 'lucide-react';
import { analytics, appointments, conversations } from '@/lib/api';

interface Stats {
  appointments_today: number;
  calls_today: number;
  messages_today: number;
  active_emergencies: number;
}

interface Appointment {
  id: string;
  start_time: string;
  pet_name?: string;
  client_name?: string;
  reason?: string;
  status: string;
}

interface Conversation {
  id: string;
  channel: string;
  status: string;
  started_at: string;
  client_phone?: string;
  message_count: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [recentConversations, setRecentConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const [statsData, appointmentsData, conversationsData] = await Promise.all([
        analytics.getToday().catch(() => null),
        appointments.list({ start_date: today, end_date: today }).catch(() => []),
        conversations.list({ limit: 5 }).catch(() => []),
      ]);

      setStats(statsData || { appointments_today: 0, calls_today: 0, messages_today: 0, active_emergencies: 0 });
      setTodayAppointments(Array.isArray(appointmentsData) ? appointmentsData : []);
      setRecentConversations(Array.isArray(conversationsData) ? conversationsData : []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatTime = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '--:--';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Panel de Control</h1>
        <button
          onClick={fetchData}
          className="p-2 border rounded hover:bg-gray-100"
          title="Actualizar"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link href="/appointments" className="p-4 bg-white border rounded-lg hover:shadow-md">
          <div className="flex items-center gap-3">
            <Calendar className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.appointments_today || 0}</p>
              <p className="text-sm text-gray-500">Citas hoy</p>
            </div>
          </div>
        </Link>

        <Link href="/conversations" className="p-4 bg-white border rounded-lg hover:shadow-md">
          <div className="flex items-center gap-3">
            <MessageCircle className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.messages_today || 0}</p>
              <p className="text-sm text-gray-500">Mensajes</p>
            </div>
          </div>
        </Link>

        <Link href="/chat" className="p-4 bg-white border rounded-lg hover:shadow-md">
          <div className="flex items-center gap-3">
            <Bot className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.calls_today || 0}</p>
              <p className="text-sm text-gray-500">Llamadas IA</p>
            </div>
          </div>
        </Link>

        <Link href="/clients" className="p-4 bg-white border rounded-lg hover:shadow-md">
          <div className="flex items-center gap-3">
            <Users className="h-8 w-8 text-orange-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.active_emergencies || 0}</p>
              <p className="text-sm text-gray-500">Emergencias</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Two Column Layout */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Today's Appointments */}
        <div className="bg-white border rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-semibold">Citas de Hoy</h2>
            <Link href="/appointments" className="text-blue-600 text-sm hover:underline">
              Ver todas →
            </Link>
          </div>

          {todayAppointments.length === 0 ? (
            <p className="text-gray-500 text-sm py-4 text-center">No hay citas para hoy</p>
          ) : (
            <div className="space-y-3">
              {todayAppointments.slice(0, 5).map((apt) => (
                <div key={apt.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium">{formatTime(apt.start_time)}</p>
                    <p className="text-sm text-gray-600">
                      {apt.pet_name || 'Sin nombre'} - {apt.reason || 'Consulta'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${
                    apt.status === 'cancelled' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {apt.status === 'cancelled' ? 'Cancelada' : 'Programada'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="bg-white border rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-semibold">Conversaciones Recientes</h2>
            <Link href="/conversations" className="text-blue-600 text-sm hover:underline">
              Ver todas →
            </Link>
          </div>

          {recentConversations.length === 0 ? (
            <p className="text-gray-500 text-sm py-4 text-center">No hay conversaciones recientes</p>
          ) : (
            <div className="space-y-3">
              {recentConversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/conversations/${conv.id}`}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <MessageCircle className={`h-4 w-4 ${
                      conv.status === 'active' ? 'text-green-500' : 'text-gray-400'
                    }`} />
                    <div>
                      <p className="font-medium text-sm">{conv.client_phone || 'Sin número'}</p>
                      <p className="text-xs text-gray-500">{conv.message_count} mensajes</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${
                    conv.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {conv.status === 'active' ? 'Activa' : 'Cerrada'}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold mb-3">Acciones Rápidas</h3>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/appointments"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Nueva Cita
          </Link>
          <Link
            href="/chat"
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Chat con IA
          </Link>
          <Link
            href="/clients"
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Ver Clientes
          </Link>
        </div>
      </div>
    </div>
  );
}
