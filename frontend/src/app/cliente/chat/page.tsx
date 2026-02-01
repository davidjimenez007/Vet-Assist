'use client';

import { useEffect, useRef, useState } from 'react';
import { Send, RotateCcw, Bot, User, CalendarCheck } from 'lucide-react';
import { clientApi } from '@/lib/clientApi';
import { useClientAuth } from '@/lib/clientAuth';

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
  appointmentBooked?: boolean;
}

const SUGGESTED_PROMPTS = [
  'Quiero agendar una cita',
  'Ver mis proximas citas',
  'Mi mascota tiene una emergencia',
  'Horarios de la clinica',
];

export default function ClienteChatPage() {
  const { client } = useClientAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [appointmentBooked, setAppointmentBooked] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startNewConversation = async () => {
    setIsStarting(true);
    setAppointmentBooked(false);
    try {
      const response = await clientApi.newConversation();
      setConversationId(response.conversation_id);
      setMessages([
        {
          role: 'assistant',
          content: response.message,
        },
      ]);
    } catch (error) {
      console.error('Error starting conversation:', error);
      setMessages([
        {
          role: 'assistant',
          content: 'Error al conectar con el asistente. Por favor intenta de nuevo.',
        },
      ]);
    } finally {
      setIsStarting(false);
      inputRef.current?.focus();
    }
  };

  useEffect(() => {
    startNewConversation();
  }, []);

  const handleSend = async (messageText?: string) => {
    const trimmedInput = (messageText || input).trim();
    if (!trimmedInput || isLoading) return;

    const userMessage: Message = { role: 'user', content: trimmedInput };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await clientApi.sendMessage(
        trimmedInput,
        conversationId || undefined
      );

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        appointmentBooked: response.appointment_booked,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.appointment_booked) {
        setAppointmentBooked(true);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Error al procesar el mensaje. Intenta de nuevo.',
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    setMessages([]);
    setConversationId(null);
    setAppointmentBooked(false);
    startNewConversation();
  };

  const handleSuggestedPrompt = (prompt: string) => {
    handleSend(prompt);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Appointment Booked Banner */}
      {appointmentBooked && (
        <div className="m-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl flex items-center gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
            <CalendarCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-green-800 dark:text-green-200 text-sm">
              Cita agendada
            </p>
            <p className="text-xs text-green-600 dark:text-green-400">
              Puedes verla en la seccion de Citas
            </p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isStarting ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <div className="animate-pulse">Conectando...</div>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400 dark:text-gray-500">
              <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Iniciando...</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : msg.appointmentBooked
                      ? 'bg-green-100 dark:bg-green-900/30 text-gray-900 dark:text-gray-100 border border-green-200 dark:border-green-800'
                      : 'bg-white dark:bg-dark-surface text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-dark-border'
                  }`}
                >
                  {msg.appointmentBooked && (
                    <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400 text-xs font-medium mb-1">
                      <CalendarCheck className="h-3.5 w-3.5" />
                      Cita confirmada
                    </div>
                  )}
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
                {msg.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                    <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggested Prompts */}
      {messages.length <= 2 && !isLoading && !isStarting && (
        <div className="px-4 pb-2">
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestedPrompt(prompt)}
                className="px-3 py-1.5 text-xs bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface p-4">
        <div className="flex items-center gap-3 max-w-2xl mx-auto">
          <button
            onClick={handleReset}
            className="p-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Nueva conversacion"
          >
            <RotateCcw className="h-5 w-5" />
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu mensaje..."
            className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isLoading || isStarting}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading || isStarting}
            className="p-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
