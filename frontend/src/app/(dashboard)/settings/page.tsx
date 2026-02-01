'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Clock, Users, AlertTriangle, ChevronRight } from 'lucide-react';
import Card from '@/components/ui/Card';
import { settings, clinic } from '@/lib/api';

interface ClinicData {
  name: string;
  phone: string;
  timezone: string;
}

export default function SettingsPage() {
  const [clinicData, setClinicData] = useState<ClinicData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await clinic.get();
        setClinicData(data);
      } catch (error) {
        console.error('Error fetching clinic data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const settingsLinks = [
    {
      href: '/settings/hours',
      icon: Clock,
      title: 'Horarios de atencion',
      description: 'Configura los dias y horas de atencion de la clinica',
    },
    {
      href: '/settings/staff',
      icon: Users,
      title: 'Equipo',
      description: 'Administra veterinarios y personal de la clinica',
    },
    {
      href: '/settings/escalation',
      icon: AlertTriangle,
      title: 'Contactos de emergencia',
      description: 'Configura quien recibe alertas de emergencia',
    },
  ];

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
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Configuracion
      </h1>

      {/* Clinic info */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Informacion de la clinica
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
              Nombre
            </label>
            <p className="text-gray-900 dark:text-gray-100">
              {clinicData?.name || '-'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
              Telefono
            </label>
            <p className="text-gray-900 dark:text-gray-100">
              {clinicData?.phone || '-'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
              Zona horaria
            </label>
            <p className="text-gray-900 dark:text-gray-100">
              {clinicData?.timezone || 'America/Bogota'}
            </p>
          </div>
        </div>
      </Card>

      {/* Settings links */}
      <div className="space-y-3">
        {settingsLinks.map((item) => (
          <Link key={item.href} href={item.href}>
            <Card className="flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-lg">
                  <item.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {item.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {item.description}
                  </p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-gray-400" />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
