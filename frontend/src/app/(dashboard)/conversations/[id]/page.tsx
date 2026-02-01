'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Phone, MessageCircle, AlertTriangle, User, Bot, RefreshCw, Send, UserCog } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { conversations } from '@/lib/api';
import {
  formatDate,
  formatTime,
  formatPhone,
  translateStatus,
  translateOutcome,
  getStatusColor,
  cn,
} from '@/lib/utils';

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Conversation {
  id: string;
  channel: string;
  status: string;
  outcome?: string;
  intent?: string;
  started_at: string;
  ended_at?: string;
  client_phone?: string;
  client_name?: string;
  message_count: number;
}

export default function ConversationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchData = async (showLoading = true) => {
    if (showLoading) setIsRefreshing(true);
    try {
      const [convData, messagesData] = await Promise.all([
        conversations.get(params.id as string),
        conversations.getMessages(params.id as string),
      ]);
      setConversation(convData);
      setMessages(messagesData);
    } catch (error) {
      console.error('Error fetching conversation:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [params.id]);

  // Auto-refresh for active conversations
  useEffect(() => {
    if (conversation?.status === 'active') {
      const interval = setInterval(() => fetchData(false), 5000);
      return () => clearInterval(interval);
    }
  }, [conversation?.status, params.id]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getChannelIcon = (channel: string, status: string) => {
    if (status === 'escalated') {
      return <AlertTriangle className="h-5 w-5 text-red-500" />;
    }
    return channel === 'voice' ? (
      <Phone className="h-5 w-5 text-blue-500" />
    ) : (
      <MessageCircle className="h-5 w-5 text-green-500" />
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          Conversacion no encontrada
        </p>
      </div>
    );
  }

  const isActive = conversation.status === 'active';

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
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Conversacion
            </h1>
            {isActive && (
              <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                En vivo - actualizando cada 5s
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchData(true)}
            disabled={isRefreshing}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Actualizar"
          >
            <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Live conversation banner */}
      {isActive && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
                <MessageCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="font-medium text-green-800 dark:text-green-200">
                  Conversacion activa
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">
                  La IA esta manejando esta conversacion por {conversation.channel === 'whatsapp' ? 'WhatsApp' : 'llamada'}
                </p>
              </div>
            </div>
            <Button variant="secondary" size="sm" className="flex items-center gap-2">
              <UserCog className="h-4 w-4" />
              Tomar control
            </Button>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        {/* Conversation info */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
              {getChannelIcon(conversation.channel, conversation.status)}
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {conversation.channel === 'voice' ? 'Llamada' : 'WhatsApp'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {formatDate(conversation.started_at, "d MMM yyyy, HH:mm")}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Estado
              </label>
              <Badge className={getStatusColor(conversation.status)}>
                {translateStatus(conversation.status)}
              </Badge>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Cliente
              </label>
              <p className="text-gray-900 dark:text-gray-100">
                {conversation.client_name || formatPhone(conversation.client_phone || 'Desconocido')}
              </p>
            </div>

            {conversation.intent && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Intencion detectada
                </label>
                <p className="text-gray-900 dark:text-gray-100 capitalize">
                  {conversation.intent.toLowerCase()}
                </p>
              </div>
            )}

            {conversation.outcome && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                  Resultado
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {translateOutcome(conversation.outcome)}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Duracion
              </label>
              <p className="text-gray-900 dark:text-gray-100">
                {conversation.ended_at
                  ? `${Math.round(
                      (new Date(conversation.ended_at).getTime() -
                        new Date(conversation.started_at).getTime()) /
                        60000
                    )} minutos`
                  : 'En curso'}
              </p>
            </div>
          </div>
        </Card>

        {/* Messages */}
        <Card className="md:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Transcripcion
          </h2>

          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No hay mensajes
              </p>
            ) : (
              <>
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      'flex gap-3',
                      msg.role === 'user' ? 'flex-row-reverse' : ''
                    )}
                  >
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                        msg.role === 'user'
                          ? 'bg-primary-100 dark:bg-primary-900'
                          : 'bg-gray-100 dark:bg-gray-800'
                      )}
                    >
                      {msg.role === 'user' ? (
                        <User className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                      ) : (
                        <Bot className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                      )}
                    </div>
                    <div
                      className={cn(
                        'max-w-[80%] p-3 rounded-lg',
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                      )}
                    >
                      <p className="text-sm">{msg.content}</p>
                      <p
                        className={cn(
                          'text-xs mt-1',
                          msg.role === 'user'
                            ? 'text-primary-200'
                            : 'text-gray-500 dark:text-gray-400'
                        )}
                      >
                        {formatTime(msg.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
