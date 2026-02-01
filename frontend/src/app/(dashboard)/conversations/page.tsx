'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Phone, MessageCircle, AlertTriangle, Filter } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { conversations } from '@/lib/api';
import {
  formatDate,
  formatRelative,
  formatPhone,
  translateStatus,
  translateOutcome,
  getStatusColor,
} from '@/lib/utils';

interface Conversation {
  id: string;
  channel: string;
  status: string;
  outcome?: string;
  started_at: string;
  ended_at?: string;
  client_phone?: string;
  client_name?: string;
  message_count: number;
}

export default function ConversationsPage() {
  const [conversationList, setConversationList] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      try {
        const params: { channel?: string; limit: number } = { limit: 50 };
        if (filter) {
          params.channel = filter;
        }
        const data = await conversations.list(params);
        // Ensure data is an array and filter out invalid items
        const validData = Array.isArray(data) ? data.filter(conv => conv && conv.id && conv.started_at) : [];
        setConversationList(validData);
      } catch (error) {
        console.error('Error fetching conversations:', error);
        setConversationList([]); // Set empty array on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [filter]);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Conversaciones
        </h1>
        <div className="flex items-center gap-2">
          <Button
            variant={filter === null ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter(null)}
          >
            Todas
          </Button>
          <Button
            variant={filter === 'voice' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('voice')}
          >
            <Phone className="h-4 w-4 mr-1" />
            Llamadas
          </Button>
          <Button
            variant={filter === 'whatsapp' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('whatsapp')}
          >
            <MessageCircle className="h-4 w-4 mr-1" />
            WhatsApp
          </Button>
        </div>
      </div>

      {/* Conversations list */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
        </div>
      ) : conversationList.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No hay conversaciones
          </p>
        </Card>
      ) : (
        <Card className="divide-y divide-gray-100 dark:divide-gray-800">
          {conversationList.map((conv) => (
            <Link
              key={conv.id}
              href={`/conversations/${conv.id}`}
              className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors -mx-6 px-6 first:-mt-6 first:pt-6 last:-mb-6 last:pb-6"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  {getChannelIcon(conv.channel, conv.status)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {formatPhone(conv.client_phone || 'Desconocido')}
                    </span>
                    {conv.client_name && (
                      <span className="text-gray-500 dark:text-gray-400">
                        ({conv.client_name})
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {conv.outcome
                      ? translateOutcome(conv.outcome)
                      : `${conv.message_count} mensajes`}{' '}
                    - {formatRelative(conv.started_at)}
                  </p>
                </div>
              </div>
              <Badge className={getStatusColor(conv.status)}>
                {translateStatus(conv.status)}
              </Badge>
            </Link>
          ))}
        </Card>
      )}
    </div>
  );
}
