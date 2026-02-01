import Link from 'next/link';
import {
  Phone,
  MessageCircle,
  Calendar,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Bot,
  Clock,
  Users,
  CheckCircle,
  Zap,
  Shield,
  BarChart3,
  Settings
} from 'lucide-react';

export default function ComoFuncionaPage() {
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
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver
            </Link>
            <Link
              href="/solicitar-demo"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Solicitar Demo
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-16 bg-gradient-to-b from-primary-50 to-white dark:from-dark-surface dark:to-dark-bg">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-6">
            Como funciona VetAssist
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Descubre como nuestra IA puede transformar la atencion al cliente de tu clinica veterinaria
          </p>
        </div>
      </section>

      {/* Flujo Principal - Diagrama Visual */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-4">
            El flujo de atencion automatizada
          </h2>
          <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            Desde que un cliente contacta hasta que su cita queda agendada, todo en segundos
          </p>

          {/* Diagrama de flujo */}
          <div className="max-w-5xl mx-auto">
            <div className="grid md:grid-cols-5 gap-4 items-center">
              {/* Paso 1 */}
              <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border-2 border-blue-200 dark:border-blue-800">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-8 w-8 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">1. Contacto</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cliente llama o escribe por WhatsApp
                </p>
              </div>

              {/* Flecha */}
              <div className="hidden md:flex justify-center">
                <ArrowRight className="h-8 w-8 text-gray-400" />
              </div>

              {/* Paso 2 */}
              <div className="text-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-2xl border-2 border-purple-200 dark:border-purple-800">
                <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Bot className="h-8 w-8 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">2. IA Responde</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Entiende la necesidad y responde naturalmente
                </p>
              </div>

              {/* Flecha */}
              <div className="hidden md:flex justify-center">
                <ArrowRight className="h-8 w-8 text-gray-400" />
              </div>

              {/* Paso 3 */}
              <div className="text-center p-6 bg-green-50 dark:bg-green-900/20 rounded-2xl border-2 border-green-200 dark:border-green-800">
                <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Calendar className="h-8 w-8 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">3. Agenda</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cita confirmada automaticamente
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Canales de comunicacion */}
      <section className="py-20 bg-gray-50 dark:bg-dark-surface">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-4">
            Multiples canales, una sola plataforma
          </h2>
          <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            Atiende a tus clientes donde ellos prefieran comunicarse
          </p>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Llamadas de voz */}
            <div className="bg-white dark:bg-dark-bg rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-dark-border">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-blue-100 dark:bg-blue-900 rounded-xl flex items-center justify-center">
                  <Phone className="h-7 w-7 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Llamadas de Voz
                </h3>
              </div>
              <ul className="space-y-3">
                {[
                  'Contesta en espanol colombiano natural',
                  'Entiende acentos y modismos locales',
                  'Transcribe y guarda cada conversacion',
                  'Detecta tono de urgencia en la voz',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-600 dark:text-gray-400">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* WhatsApp */}
            <div className="bg-white dark:bg-dark-bg rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-dark-border">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-green-100 dark:bg-green-900 rounded-xl flex items-center justify-center">
                  <MessageCircle className="h-7 w-7 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  WhatsApp
                </h3>
              </div>
              <ul className="space-y-3">
                {[
                  'Respuestas instantaneas 24/7',
                  'Envia confirmaciones automaticas',
                  'Comparte horarios disponibles',
                  'Recordatorios de citas programados',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-600 dark:text-gray-400">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Funcionalidades detalladas */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-4">
            Funcionalidades principales
          </h2>
          <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            Todo lo que necesitas para automatizar la recepcion de tu clinica
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {[
              {
                icon: Calendar,
                title: 'Agendamiento Inteligente',
                description: 'Agenda citas automaticamente verificando disponibilidad en tiempo real. Cero cruces de horarios.',
                color: 'blue',
              },
              {
                icon: AlertTriangle,
                title: 'Deteccion de Emergencias',
                description: 'Identifica palabras clave de urgencia y te notifica inmediatamente por SMS y llamada.',
                color: 'red',
              },
              {
                icon: Users,
                title: 'Gestion de Clientes',
                description: 'Crea y actualiza fichas de clientes y mascotas automaticamente durante la conversacion.',
                color: 'purple',
              },
              {
                icon: Clock,
                title: 'Disponible 24/7',
                description: 'Nunca pierdas una llamada. Atiende fuera de horario y agenda para el siguiente dia habil.',
                color: 'green',
              },
              {
                icon: BarChart3,
                title: 'Dashboard Analitico',
                description: 'Visualiza metricas de llamadas, citas agendadas, emergencias y mas en tiempo real.',
                color: 'orange',
              },
              {
                icon: Settings,
                title: 'Configuracion Flexible',
                description: 'Personaliza horarios, tipos de cita, duraciones y mensajes segun tu clinica.',
                color: 'gray',
              },
            ].map((feature, i) => {
              const colors: Record<string, string> = {
                blue: 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400',
                red: 'bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400',
                purple: 'bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400',
                green: 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400',
                orange: 'bg-orange-100 dark:bg-orange-900 text-orange-600 dark:text-orange-400',
                gray: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
              };
              return (
                <div
                  key={i}
                  className="p-6 bg-white dark:bg-dark-surface rounded-xl border border-gray-200 dark:border-dark-border hover:shadow-lg transition-shadow"
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${colors[feature.color]}`}>
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Proceso de implementacion */}
      <section className="py-20 bg-gray-50 dark:bg-dark-surface">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-gray-100 mb-4">
            Implementacion en 3 pasos
          </h2>
          <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            Comienza a usar VetAssist en menos de 24 horas
          </p>

          <div className="max-w-4xl mx-auto">
            <div className="relative">
              {/* Linea conectora */}
              <div className="hidden md:block absolute top-24 left-1/2 w-full h-0.5 bg-primary-200 dark:bg-primary-800 -translate-x-1/2" style={{ width: '66%' }} />

              <div className="grid md:grid-cols-3 gap-8">
                {[
                  {
                    step: '1',
                    title: 'Solicita tu Demo',
                    description: 'Agenda una llamada con nuestro equipo. Te mostramos como funciona en vivo.',
                    time: '30 min',
                  },
                  {
                    step: '2',
                    title: 'Configuracion',
                    description: 'Conectamos tu numero de telefono y WhatsApp. Configuramos horarios y servicios.',
                    time: '2-4 horas',
                  },
                  {
                    step: '3',
                    title: 'En Vivo',
                    description: 'VetAssist comienza a atender llamadas. Tu solo supervisas desde el dashboard.',
                    time: 'Inmediato',
                  },
                ].map((item) => (
                  <div key={item.step} className="relative text-center">
                    <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
                      <span className="text-2xl font-bold text-white">{item.step}</span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                      {item.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-2">
                      {item.description}
                    </p>
                    <span className="inline-block px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-sm font-medium">
                      {item.time}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Seguridad y confianza */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto bg-gradient-to-r from-primary-600 to-primary-700 rounded-3xl p-8 md:p-12 text-white">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="flex-shrink-0">
                <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
                  <Shield className="h-10 w-10" />
                </div>
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-3">Seguridad y Privacidad</h3>
                <p className="text-primary-100 mb-4">
                  Tus datos y los de tus clientes estan protegidos. Cumplimos con las regulaciones
                  de proteccion de datos. Todas las conversaciones son encriptadas y almacenadas de forma segura.
                </p>
                <div className="flex flex-wrap gap-4">
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Encriptacion SSL</span>
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Datos en Colombia</span>
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">Backups diarios</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-20 bg-gray-50 dark:bg-dark-surface">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Listo para automatizar tu clinica?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-xl mx-auto">
            Solicita una demo gratuita y descubre como VetAssist puede ayudarte a atender mas clientes con menos esfuerzo.
          </p>
          <Link
            href="/solicitar-demo"
            className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-lg"
          >
            Solicitar Demo Gratuita
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-gray-600 dark:text-gray-400">
              2024 VetAssist. Todos los derechos reservados.
            </div>
            <div className="flex items-center gap-6">
              <Link href="/" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
                Inicio
              </Link>
              <Link href="/solicitar-demo" className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
                Solicitar Demo
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
