'use client';

import Link from 'next/link';
import { Phone, MessageCircle, AlertTriangle } from 'lucide-react';
import Card from '@/components/ui/Card';
import { formatRelative, formatPhone, translateOutcome } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface Conversation {
  id: string;
  channel: string;
  status: string;
  outcome?: string;
  started_at: string;
  client_phone?: string;
  message_count: number;
}

interface ConversationListProps {
  conversations: Conversation[];
  showViewAll?: boolean;
}

export default function ConversationList({
  conversations,
  showViewAll = true,
}: ConversationListProps) {
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
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Conversaciones Recientes
        </h3>
        {showViewAll && (
          <Link
            href="/conversations"
            className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            Ver todo
          </Link>
        )}
      </div>

      <div className="space-y-3">
        {conversations.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm py-4 text-center">
            No hay conversaciones recientes
          </p>
        ) : (
          conversations.map((conv) => (
            <Link
              key={conv.id}
              href={`/conversations/${conv.id}`}
              className={cn(
                'block p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors',
                conv.status === 'escalated' && 'bg-red-50 dark:bg-red-900/20'
              )}
            >
              <div className="flex items-start gap-3">
                {getChannelIcon(conv.channel, conv.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {formatPhone(conv.client_phone || 'Desconocido')}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatRelative(conv.started_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
                    {conv.outcome
                      ? translateOutcome(conv.outcome)
                      : `${conv.message_count} mensajes`}
                  </p>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}
