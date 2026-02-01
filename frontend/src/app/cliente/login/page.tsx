'use client';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Phone, ArrowRight, KeyRound, AlertCircle, CheckCircle } from 'lucide-react';
import { useClientAuth } from '@/lib/clientAuth';

type Step = 'phone' | 'otp';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const clinicId = searchParams.get('clinic');

  const { requestOTP, verifyOTP, isAuthenticated, checkAuth, setClinicId } = useClientAuth();

  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/cliente/citas');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (clinicId) {
      setClinicId(clinicId);
    }
  }, [clinicId, setClinicId]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '');
    return digits;
  };

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!clinicId) {
      setError('Por favor escanea el codigo QR de la clinica para continuar.');
      return;
    }

    if (!phone || phone.length < 10) {
      setError('Por favor ingresa un numero de telefono valido');
      return;
    }

    setIsLoading(true);

    try {
      const formattedPhone = phone.startsWith('+') ? phone : `+57${phone}`;
      await requestOTP(formattedPhone, clinicId);
      setSuccess('Codigo enviado por SMS');
      setStep('otp');
      setCountdown(60);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Error al enviar el codigo';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!clinicId) {
      setError('Enlace invalido. Por favor escanea el codigo QR nuevamente.');
      return;
    }

    if (!otp || otp.length !== 6) {
      setError('Por favor ingresa el codigo de 6 digitos');
      return;
    }

    setIsLoading(true);

    try {
      const formattedPhone = phone.startsWith('+') ? phone : `+57${phone}`;
      await verifyOTP(formattedPhone, clinicId, otp);
      router.push('/cliente/citas');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Codigo invalido';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;

    setError('');
    setIsLoading(true);

    try {
      const formattedPhone = phone.startsWith('+') ? phone : `+57${phone}`;
      await requestOTP(formattedPhone, clinicId!);
      setSuccess('Nuevo codigo enviado');
      setCountdown(60);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Error al reenviar el codigo';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setStep('phone');
    setOtp('');
    setError('');
    setSuccess('');
  };

  if (!clinicId) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center p-4">
        <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-8 w-8 text-amber-600 dark:text-amber-400" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Acceso al portal
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Para acceder al portal de clientes necesitas el enlace de tu clinica veterinaria.
          </p>
          <div className="bg-gray-50 dark:bg-dark-bg rounded-xl p-4 text-left space-y-3">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Como obtener acceso:
            </p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">1.</span>
                Escanea el codigo QR en la clinica
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">2.</span>
                Pide el enlace por WhatsApp a tu clinica
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">3.</span>
                Revisa el mensaje de confirmacion de tu ultima cita
              </li>
            </ul>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-6">
            Si ya tienes una cita, tu clinica te enviara el enlace automaticamente.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center p-4">
      <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-lg p-8 max-w-md w-full">
        <div className="flex justify-center mb-8">
          <div className="h-12 w-12 bg-primary-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">V</span>
          </div>
        </div>

        {step === 'phone' ? (
          <>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 text-center mb-2">
              Bienvenido
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-center mb-8">
              Ingresa tu numero de telefono para acceder
            </p>

            <form onSubmit={handlePhoneSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Numero de telefono
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Phone className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="absolute inset-y-0 left-10 flex items-center pointer-events-none">
                    <span className="text-gray-500 dark:text-gray-400">+57</span>
                  </div>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(formatPhone(e.target.value))}
                    placeholder="300 123 4567"
                    className="block w-full pl-20 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-dark-bg text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    maxLength={10}
                    autoFocus
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || phone.length < 10}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isLoading ? (
                  'Enviando...'
                ) : (
                  <>
                    Continuar
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </button>
            </form>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 text-center mb-2">
              Verificacion
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-center mb-2">
              Ingresa el codigo de 6 digitos enviado a
            </p>
            <p className="text-primary-600 dark:text-primary-400 text-center font-medium mb-8">
              +57 {phone}
            </p>

            {success && (
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm mb-4 justify-center">
                <CheckCircle className="h-4 w-4" />
                <span>{success}</span>
              </div>
            )}

            <form onSubmit={handleOTPSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Codigo de verificacion
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <KeyRound className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    className="block w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-dark-bg text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-center text-2xl tracking-widest font-mono"
                    maxLength={6}
                    autoFocus
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || otp.length !== 6}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isLoading ? 'Verificando...' : 'Verificar'}
              </button>

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={handleBack}
                  className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                >
                  Cambiar numero
                </button>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={countdown > 0 || isLoading}
                  className="text-primary-600 dark:text-primary-400 hover:text-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {countdown > 0 ? `Reenviar en ${countdown}s` : 'Reenviar codigo'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center">
      <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
    </div>
  );
}

export default function ClienteLoginPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <LoginForm />
    </Suspense>
  );
}
