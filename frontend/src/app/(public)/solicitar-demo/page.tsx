'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Phone,
  Mail,
  Building,
  User,
  MessageSquare,
  Clock,
  Calendar,
} from 'lucide-react';

interface FormData {
  clinic_name: string;
  contact_name: string;
  email: string;
  phone: string;
  clinic_size: string;
  message: string;
  preferred_time: string;
}

export default function SolicitarDemoPage() {
  const [formData, setFormData] = useState<FormData>({
    clinic_name: '',
    contact_name: '',
    email: '',
    phone: '',
    clinic_size: '',
    message: '',
    preferred_time: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      const response = await fetch('/api/demo-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          phone: `+57${formData.phone.replace(/\D/g, '')}`,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al enviar la solicitud');
      }

      setIsSubmitted(true);
    } catch (err) {
      console.error('Error submitting demo request:', err);
      setError('Hubo un error al enviar tu solicitud. Por favor intenta de nuevo.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-white dark:bg-dark-bg">
        {/* Header */}
        <header className="border-b border-gray-200 dark:border-dark-border">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">V</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
                VetAssist
              </span>
            </Link>
          </div>
        </header>

        {/* Success Message */}
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="text-center max-w-md mx-auto px-4">
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Solicitud Enviada!
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Gracias por tu interes en VetAssist. Nuestro equipo de ventas se pondra en contacto contigo
              dentro de las proximas <strong>24 horas habiles</strong> para coordinar tu demo personalizada.
            </p>
            <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl p-4 mb-8">
              <p className="text-sm text-primary-700 dark:text-primary-300">
                Mientras tanto, puedes explorar como funciona nuestra plataforma
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/como-funciona"
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-medium"
              >
                Ver como funciona
              </Link>
              <Link
                href="/"
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
              >
                Volver al inicio
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-dark-bg">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">V</span>
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
              VetAssist
            </span>
          </Link>
          <Link
            href="/"
            className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <div className="py-12 lg:py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12">
              {/* Left - Info */}
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                  Solicita tu Demo Gratuita
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
                  Agenda una llamada personalizada con nuestro equipo. Te mostraremos como VetAssist
                  puede transformar la atencion al cliente de tu clinica.
                </p>

                {/* Benefits */}
                <div className="space-y-4 mb-8">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                    En la demo incluye:
                  </h3>
                  {[
                    { icon: Phone, text: 'Demostracion en vivo de llamadas y WhatsApp' },
                    { icon: Calendar, text: 'Configuracion personalizada para tu clinica' },
                    { icon: Clock, text: 'Sesion de 30 minutos con un especialista' },
                    { icon: MessageSquare, text: 'Resolucion de todas tus dudas' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center flex-shrink-0">
                        <item.icon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                      </div>
                      <span className="text-gray-600 dark:text-gray-400">{item.text}</span>
                    </div>
                  ))}
                </div>

                {/* Trust badges */}
                <div className="bg-gray-50 dark:bg-dark-surface rounded-xl p-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                    Empresas que confian en nosotros:
                  </p>
                  <div className="flex items-center gap-4 text-gray-400">
                    <span className="font-semibold">+50 clinicas</span>
                    <span>|</span>
                    <span className="font-semibold">Colombia</span>
                  </div>
                </div>
              </div>

              {/* Right - Form */}
              <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-xl border border-gray-200 dark:border-dark-border p-6 lg:p-8">
                <form onSubmit={handleSubmit} className="space-y-5">
                  {error && (
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                    </div>
                  )}

                  {/* Clinic Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Nombre de la clinica *
                    </label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="clinic_name"
                        value={formData.clinic_name}
                        onChange={handleChange}
                        placeholder="Clinica Veterinaria ABC"
                        className="input pl-10"
                        required
                      />
                    </div>
                  </div>

                  {/* Contact Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tu nombre *
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="contact_name"
                        value={formData.contact_name}
                        onChange={handleChange}
                        placeholder="Juan Perez"
                        className="input pl-10"
                        required
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Correo electronico *
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="juan@clinica.com"
                        className="input pl-10"
                        required
                      />
                    </div>
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Telefono *
                    </label>
                    <div className="flex">
                      <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 text-gray-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400">
                        +57
                      </span>
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="300 123 4567"
                        className="input rounded-l-none"
                        required
                      />
                    </div>
                  </div>

                  {/* Clinic Size */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tamano de la clinica
                    </label>
                    <select
                      name="clinic_size"
                      value={formData.clinic_size}
                      onChange={handleChange}
                      className="input"
                    >
                      <option value="">Selecciona una opcion</option>
                      <option value="1-2">1-2 veterinarios</option>
                      <option value="3-5">3-5 veterinarios</option>
                      <option value="6-10">6-10 veterinarios</option>
                      <option value="10+">Mas de 10 veterinarios</option>
                    </select>
                  </div>

                  {/* Preferred Time */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Horario preferido para la llamada
                    </label>
                    <select
                      name="preferred_time"
                      value={formData.preferred_time}
                      onChange={handleChange}
                      className="input"
                    >
                      <option value="">Selecciona una opcion</option>
                      <option value="morning">Manana (8am - 12pm)</option>
                      <option value="afternoon">Tarde (12pm - 5pm)</option>
                      <option value="evening">Noche (5pm - 7pm)</option>
                    </select>
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Mensaje adicional (opcional)
                    </label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Cuentanos sobre tu clinica o alguna necesidad especifica..."
                      className="input min-h-[100px]"
                    />
                  </div>

                  {/* Submit */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      'Enviando...'
                    ) : (
                      <>
                        Solicitar Demo Gratuita
                        <ArrowRight className="h-5 w-5" />
                      </>
                    )}
                  </button>

                  <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                    Al enviar este formulario, aceptas que nos comuniquemos contigo para coordinar la demo.
                    No compartimos tu informacion con terceros.
                  </p>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
