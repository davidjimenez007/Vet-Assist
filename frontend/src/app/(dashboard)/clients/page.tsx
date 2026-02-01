'use client';

import { useEffect, useState } from 'react';
import {
  Plus,
  Search,
  Phone,
  Mail,
  ChevronDown,
  ChevronUp,
  PawPrint,
  Edit2,
  Trash2,
  X,
  Calendar,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { clients } from '@/lib/api';
import { formatPhone, getPetEmoji } from '@/lib/utils';

interface Pet {
  id: string;
  name: string | null;
  species: string;
  breed: string | null;
  notes: string | null;
}

interface Client {
  id: string;
  phone: string;
  name: string | null;
  email: string | null;
  created_at: string;
  pets: Pet[];
  appointment_count: number;
}

export default function ClientsPage() {
  const [clientList, setClientList] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Modal states
  const [isClientModalOpen, setIsClientModalOpen] = useState(false);
  const [isPetModalOpen, setIsPetModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [petParentId, setPetParentId] = useState<string | null>(null);

  // Form states
  const [clientForm, setClientForm] = useState({ phone: '', name: '', email: '' });
  const [petForm, setPetForm] = useState({ name: '', species: 'dog', breed: '', notes: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchClients = async () => {
    setIsLoading(true);
    try {
      const params: { search?: string } = {};
      if (searchQuery) params.search = searchQuery;
      const data = await clients.list(params);
      setClientList(data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchClients();
    }, searchQuery ? 300 : 0);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Client form handlers
  const openNewClient = () => {
    setEditingClient(null);
    setClientForm({ phone: '', name: '', email: '' });
    setFormError(null);
    setIsClientModalOpen(true);
  };

  const openEditClient = (client: Client) => {
    setEditingClient(client);
    setClientForm({
      phone: client.phone.replace('+57', ''),
      name: client.name || '',
      email: client.email || '',
    });
    setFormError(null);
    setIsClientModalOpen(true);
  };

  const handleClientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      const fullPhone = `+57${clientForm.phone.replace(/\D/g, '')}`;

      if (editingClient) {
        await clients.update(editingClient.id, {
          phone: fullPhone,
          name: clientForm.name || undefined,
          email: clientForm.email || undefined,
        });
      } else {
        await clients.create({
          phone: fullPhone,
          name: clientForm.name || undefined,
          email: clientForm.email || undefined,
        });
      }

      setIsClientModalOpen(false);
      fetchClients();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setFormError(axiosError.response?.data?.detail || 'Error al guardar');
      } else {
        setFormError('Error al guardar');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Pet form handlers
  const openNewPet = (clientId: string) => {
    setPetParentId(clientId);
    setPetForm({ name: '', species: 'dog', breed: '', notes: '' });
    setFormError(null);
    setIsPetModalOpen(true);
  };

  const handlePetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!petParentId) return;
    setFormError(null);
    setIsSubmitting(true);

    try {
      await clients.createPet(petParentId, {
        name: petForm.name || undefined,
        species: petForm.species,
        breed: petForm.breed || undefined,
        notes: petForm.notes || undefined,
      });

      setIsPetModalOpen(false);
      fetchClients();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setFormError(axiosError.response?.data?.detail || 'Error al guardar mascota');
      } else {
        setFormError('Error al guardar mascota');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeletePet = async (clientId: string, petId: string) => {
    if (!confirm('Eliminar esta mascota?')) return;
    try {
      await clients.deletePet(clientId, petId);
      fetchClients();
    } catch (error) {
      console.error('Error deleting pet:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Clientes
        </h1>
        <Button onClick={openNewClient}>
          <Plus className="h-5 w-5 mr-2" />
          Nuevo cliente
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nombre o telefono..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Client list */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-600 dark:text-gray-400">Cargando...</div>
        </div>
      ) : clientList.length === 0 ? (
        <Card className="text-center py-12">
          <PawPrint className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {searchQuery
              ? 'No se encontraron clientes'
              : 'No hay clientes registrados'}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {clientList.map((client) => (
            <Card key={client.id} className="overflow-hidden">
              {/* Client row */}
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                onClick={() =>
                  setExpandedId(expandedId === client.id ? null : client.id)
                }
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {client.name || 'Sin nombre'}
                      </h3>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        {client.pets.length} mascota{client.pets.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        <Phone className="h-3.5 w-3.5" />
                        {formatPhone(client.phone)}
                      </span>
                      {client.email && (
                        <span className="flex items-center gap-1">
                          <Mail className="h-3.5 w-3.5" />
                          {client.email}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        {client.appointment_count} cita{client.appointment_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Pet emojis */}
                    <div className="flex gap-1">
                      {client.pets.map((pet) => (
                        <span key={pet.id} className="text-lg" title={pet.name || pet.species}>
                          {getPetEmoji(pet.species)}
                        </span>
                      ))}
                    </div>
                    {expandedId === client.id ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded detail */}
              {expandedId === client.id && (
                <div className="border-t border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-gray-800/30 p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Cliente desde {formatDate(client.created_at)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openEditClient(client);
                      }}
                      className="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                      Editar cliente
                    </button>
                  </div>

                  {/* Pets */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Mascotas
                      </h4>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openNewPet(client.id);
                        }}
                        className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Agregar mascota
                      </button>
                    </div>

                    {client.pets.length === 0 ? (
                      <p className="text-sm text-gray-400 dark:text-gray-500 italic">
                        No tiene mascotas registradas
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {client.pets.map((pet) => (
                          <div
                            key={pet.id}
                            className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-2xl">
                                {getPetEmoji(pet.species)}
                              </span>
                              <div>
                                <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                                  {pet.name || 'Sin nombre'}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                  {pet.species}
                                  {pet.breed ? ` - ${pet.breed}` : ''}
                                </p>
                                {pet.notes && (
                                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                                    {pet.notes}
                                  </p>
                                )}
                              </div>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeletePet(client.id, pet.id);
                              }}
                              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                              title="Eliminar mascota"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* New/Edit Client Modal */}
      <Modal
        isOpen={isClientModalOpen}
        onClose={() => setIsClientModalOpen(false)}
        title={editingClient ? 'Editar cliente' : 'Nuevo cliente'}
      >
        <form onSubmit={handleClientSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>
            </div>
          )}

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
                value={clientForm.phone}
                onChange={(e) =>
                  setClientForm((prev) => ({ ...prev, phone: e.target.value }))
                }
                placeholder="300 123 4567"
                className="input rounded-l-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nombre
            </label>
            <Input
              type="text"
              value={clientForm.name}
              onChange={(e) =>
                setClientForm((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="Nombre del cliente"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <Input
              type="email"
              value={clientForm.email}
              onChange={(e) =>
                setClientForm((prev) => ({ ...prev, email: e.target.value }))
              }
              placeholder="correo@ejemplo.com"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsClientModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Guardando...' : editingClient ? 'Guardar' : 'Crear'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* New Pet Modal */}
      <Modal
        isOpen={isPetModalOpen}
        onClose={() => setIsPetModalOpen(false)}
        title="Agregar mascota"
      >
        <form onSubmit={handlePetSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nombre
              </label>
              <Input
                type="text"
                value={petForm.name}
                onChange={(e) =>
                  setPetForm((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Nombre de la mascota"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tipo *
              </label>
              <select
                value={petForm.species}
                onChange={(e) =>
                  setPetForm((prev) => ({ ...prev, species: e.target.value }))
                }
                className="input"
                required
              >
                <option value="dog">Perro</option>
                <option value="cat">Gato</option>
                <option value="other">Otro</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Raza
            </label>
            <Input
              type="text"
              value={petForm.breed}
              onChange={(e) =>
                setPetForm((prev) => ({ ...prev, breed: e.target.value }))
              }
              placeholder="Ej: Golden Retriever"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Notas
            </label>
            <textarea
              value={petForm.notes}
              onChange={(e) =>
                setPetForm((prev) => ({ ...prev, notes: e.target.value }))
              }
              placeholder="Notas sobre la mascota..."
              className="input min-h-[60px]"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsPetModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Guardando...' : 'Agregar'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
