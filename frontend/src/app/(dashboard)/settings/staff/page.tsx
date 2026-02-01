'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Trash2, Edit } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { clinic } from '@/lib/api';

interface Staff {
  id: string;
  name: string;
  role: string;
  phone?: string;
  email?: string;
  is_on_call: boolean;
}

export default function StaffPage() {
  const router = useRouter();
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    role: 'veterinarian',
    phone: '',
    email: '',
    is_on_call: false,
  });

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      const data = await clinic.listStaff();
      setStaffList(data);
    } catch (error) {
      console.error('Error fetching staff:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await clinic.createStaff(formData);
      setIsModalOpen(false);
      setFormData({
        name: '',
        role: 'veterinarian',
        phone: '',
        email: '',
        is_on_call: false,
      });
      fetchStaff();
    } catch (error) {
      console.error('Error creating staff:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Esta seguro de eliminar este miembro del equipo?')) return;
    try {
      await clinic.deleteStaff(id);
      fetchStaff();
    } catch (error) {
      console.error('Error deleting staff:', error);
    }
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      veterinarian: 'Veterinario',
      assistant: 'Asistente',
      admin: 'Administrador',
    };
    return labels[role] || role;
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
            Equipo
          </h1>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Agregar
        </Button>
      </div>

      {/* Staff list */}
      {staffList.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No hay miembros del equipo registrados
          </p>
        </Card>
      ) : (
        <Card className="divide-y divide-gray-100 dark:divide-gray-800">
          {staffList.map((staff) => (
            <div
              key={staff.id}
              className="flex items-center justify-between p-4 -mx-6 px-6 first:-mt-6 first:pt-6 last:-mb-6 last:pb-6"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {staff.name}
                  </span>
                  <Badge>{getRoleLabel(staff.role)}</Badge>
                  {staff.is_on_call && (
                    <Badge variant="success">De turno</Badge>
                  )}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {staff.email} {staff.phone && `- ${staff.phone}`}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                  <Edit className="h-4 w-4 text-gray-500" />
                </button>
                <button
                  onClick={() => handleDelete(staff.id)}
                  className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </button>
              </div>
            </div>
          ))}
        </Card>
      )}

      {/* Add staff modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Agregar miembro del equipo"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nombre"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Rol
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="input"
            >
              <option value="veterinarian">Veterinario</option>
              <option value="assistant">Asistente</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <Input
            label="Telefono"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          />
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.is_on_call}
              onChange={(e) => setFormData({ ...formData, is_on_call: e.target.checked })}
              className="w-4 h-4 text-primary-600 rounded"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Esta de turno para emergencias
            </span>
          </label>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit">Guardar</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
