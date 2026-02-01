import Link from 'next/link';
import { Phone, MessageCircle, Calendar, AlertTriangle, ArrowRight, Check, User, Stethoscope } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-dark-bg">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">V</span>
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
              VetAssist
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/como-funciona"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            >
              Como funciona
            </Link>
            <Link
              href="/login"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-1"
            >
              <Stethoscope className="h-4 w-4" />
              Veterinarios
            </Link>
            <Link
              href="/solicitar-demo"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Demo
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 lg:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 dark:text-gray-100 mb-6">
              Tu recepcionista que{' '}
              <span className="text-primary-600">nunca descansa</span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
              Atiende llamadas y WhatsApp 24/7. Agenda citas automaticamente.
              Detecta emergencias al instante.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/solicitar-demo"
                className="w-full sm:w-auto px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium flex items-center justify-center gap-2"
              >
                Solicitar demo
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/como-funciona"
                className="w-full sm:w-auto px-8 py-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-medium"
              >
                Ver como funciona
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="py-12 bg-gray-50 dark:bg-dark-surface border-y border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { value: '+2,400', label: 'citas agendadas' },
              { value: '98%', label: 'precision' },
              { value: '24/7', label: 'disponible' },
              { value: '<2s', label: 'respuesta' },
            ].map((metric, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                  {metric.value}
                </div>
                <div className="text-gray-600 dark:text-gray-400">
                  {metric.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-12">
            Como funciona
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Conecta',
                description:
                  'Vincula tu numero de telefono y WhatsApp de la clinica',
              },
              {
                step: '2',
                title: 'Configura',
                description:
                  'Define horarios, tipos de citas y contactos de emergencia',
              },
              {
                step: '3',
                title: 'Listo',
                description:
                  'El asistente atiende todas las llamadas y mensajes automaticamente',
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-primary-600 dark:text-primary-400 font-bold">
                    {item.step}
                  </span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {item.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50 dark:bg-dark-surface">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-12">
            Funcionalidades
          </h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {[
              {
                icon: Phone,
                title: 'Llamadas de voz',
                description:
                  'Contesta automaticamente en espanol colombiano natural',
              },
              {
                icon: MessageCircle,
                title: 'WhatsApp',
                description: 'Responde mensajes y agenda citas por chat',
              },
              {
                icon: Calendar,
                title: 'Agenda inteligente',
                description: 'Cero cruces de horarios, respeta tus tiempos',
              },
              {
                icon: AlertTriangle,
                title: 'Deteccion de emergencias',
                description: 'Identifica urgencias y te alerta inmediatamente',
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="flex gap-4 p-6 bg-white dark:bg-dark-bg rounded-xl border border-gray-200 dark:border-dark-border"
              >
                <div className="h-12 w-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center flex-shrink-0">
                  <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Portal Access */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-4">
            Accede a tu portal
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Selecciona tu tipo de acceso para continuar
          </p>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Client Portal */}
            <div className="bg-white dark:bg-dark-surface rounded-2xl border border-gray-200 dark:border-dark-border p-8 text-center hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <User className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Soy Cliente
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
                Accede para ver tus citas y chatear con la clinica
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mb-4">
                Escanea el codigo QR de tu clinica para acceder
              </p>
              <div className="p-4 bg-gray-50 dark:bg-dark-bg rounded-xl">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  El acceso de clientes requiere el enlace de tu clinica veterinaria
                </p>
              </div>
            </div>

            {/* Veterinary Portal */}
            <div className="bg-white dark:bg-dark-surface rounded-2xl border border-gray-200 dark:border-dark-border p-8 text-center hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Stethoscope className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Soy Veterinario
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
                Accede al dashboard para gestionar tu clinica
              </p>
              <Link
                href="/login"
                className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors font-medium"
              >
                Iniciar sesion
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/solicitar-demo"
                className="inline-block mt-3 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
              >
                No tienes cuenta? Solicita una demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gray-50 dark:bg-dark-surface">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Listo para tener mas tiempo para lo que importa?
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-8">
              Prueba VetAssist gratis por 14 dias. Sin tarjeta de credito.
            </p>
            <Link
              href="/solicitar-demo"
              className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Solicitar demo gratuita
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-gray-600 dark:text-gray-400">
              2026 VetAssist. Todos los derechos reservados.
            </div>
            <div className="flex items-center gap-6">
              <Link
                href="/como-funciona"
                className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              >
                Como funciona
              </Link>
              <Link
                href="/solicitar-demo"
                className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              >
                Contacto
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
