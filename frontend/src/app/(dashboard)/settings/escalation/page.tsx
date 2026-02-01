'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Trash2, GripVertical, Save } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { settings } from '@/lib/api';

interface EscalationContact {
  name: string;
  phone: string;
  role: string;
  priority: number;
}

export default function EscalationPage() {
  const router = useRouter();
  const [contacts, setContacts] = useState<EscalationContact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const data = await settings.getEscalation();
        setContacts(data || []);
      } catch (error) {
        console.error('Error fetching escalation contacts:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchContacts();
  }, []);

  const addContact = () => {
    setContacts([
      ...contacts,
      {
        name: '',
        phone: '',
        role: 'veterinarian',
        priority: contacts.length + 1,
      },
    ]);
  };

  const updateContact = (index: number, field: keyof EscalationContact, value: string | number) => {
    const newContacts = [...contacts];
    newContacts[index] = { ...newContacts[index], [field]: value };
    setContacts(newContacts);
  };

  const removeContact = (index: number) => {
    const newContacts = contacts.filter((_, i) => i !== index);
    // Update priorities
    newContacts.forEach((c, i) => (c.priority = i + 1));
    setContacts(newContacts);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await settings.updateEscalation(contacts);
      router.push('/settings');
    } catch (error) {
      console.error('Error saving contacts:', error);
    } finally {
      setIsSaving(false);
    }
  };

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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Contactos de emergencia
          </h1>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          <Save className="h-4 w-4 mr-2" />
          {isSaving ? 'Guardando...' : 'Guardar'}
        </Button>
      </div>

      <p className="text-gray-600 dark:text-gray-400">
        Estos contactos seran notificados en orden de prioridad cuando se detecte una emergencia.
      </p>

      {/* Contacts list */}
      <Card>
        <div className="space-y-4">
          {contacts.map((contact, index) => (
            <div
              key={index}
              className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div className="flex items-center gap-2 text-gray-400">
                <GripVertical className="h-5 w-5 cursor-move" />
                <span className="font-medium">{index + 1}</span>
              </div>
              <div className="flex-1 grid md:grid-cols-3 gap-4">
                <Input
                  placeholder="Nombre"
                  value={contact.name}
                  onChange={(e) => updateContact(index, 'name', e.target.value)}
                />
                <Input
                  placeholder="Telefono"
                  value={contact.phone}
                  onChange={(e) => updateContact(index, 'phone', e.target.value)}
                />
                <select
                  value={contact.role}
                  onChange={(e) => updateContact(index, 'role', e.target.value)}
                  className="input"
                >
                  <option value="veterinarian">Veterinario</option>
                  <option value="assistant">Asistente</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
              <button
                onClick={() => removeContact(index)}
                className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </button>
            </div>
          ))}

          <Button variant="secondary" onClick={addContact} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Agregar contacto
          </Button>
        </div>
      </Card>
    </div>
  );
}
