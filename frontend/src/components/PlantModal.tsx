import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import type { Plant, PlantInput } from '../types';
import { Button, Field, Modal, inputClass } from './ui';

const STAGES = ['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Mature', 'Dormant'];

const EMPTY: PlantInput = {
  name: '', species: '', growth_stage: 'Vegetative', age_days: 30,
  watering_frequency: '', light_condition: '', notes: '',
};

export function PlantModal({ open, onOpenChange, plant, onSaved }: {
  open: boolean; onOpenChange: (open: boolean) => void;
  plant: Plant | null; onSaved?: () => void;
}) {
  const [form, setForm] = useState<PlantInput>(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(plant ? {
        name: plant.name, species: plant.species, growth_stage: plant.growth_stage,
        age_days: plant.age_days, watering_frequency: plant.watering_frequency,
        light_condition: plant.light_condition, notes: plant.notes,
      } : EMPTY);
    }
  }, [open, plant]);

  const set = (key: keyof PlantInput) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: key === 'age_days' ? Number(e.target.value) || 0 : e.target.value }));

  const submit = async () => {
    if (!form.name.trim() || !form.species.trim() || !form.watering_frequency.trim() || !form.light_condition.trim()) {
      toast.error('Please fill in name, species, watering frequency and light condition.');
      return;
    }
    setSaving(true);
    try {
      if (plant) {
        await api.updatePlant(plant.id, form);
        toast.success(`Updated "${form.name}".`);
      } else {
        const created = await api.createPlant(form);
        toast.success(`Added "${created.name}".`);
      }
      onOpenChange(false);
      onSaved?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange} title={plant ? 'Edit Plant' : 'Add Plant'}>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Plant Name">
          <input className={inputClass} value={form.name} onChange={set('name')} placeholder="Tomato #17" />
        </Field>
        <Field label="Species">
          <input className={inputClass} value={form.species} onChange={set('species')} placeholder="Tomato" />
        </Field>
        <Field label="Growth Stage">
          <select className={inputClass} value={form.growth_stage} onChange={set('growth_stage')}>
            {STAGES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </Field>
        <Field label="Age (days)">
          <input type="number" min={0} className={inputClass} value={form.age_days} onChange={set('age_days')} />
        </Field>
        <Field label="Watering Frequency">
          <input className={inputClass} value={form.watering_frequency} onChange={set('watering_frequency')} placeholder="Every 2 days" />
        </Field>
        <Field label="Light Condition">
          <input className={inputClass} value={form.light_condition} onChange={set('light_condition')} placeholder="Bright, indirect" />
        </Field>
        <div className="col-span-2">
          <Field label="Notes">
            <textarea className={`${inputClass} min-h-20`} value={form.notes} onChange={set('notes')}
              placeholder="Anything notable about this plant…" />
          </Field>
        </div>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" onClick={() => onOpenChange(false)}>Cancel</Button>
        <Button onClick={submit} disabled={saving}>{saving ? 'Saving…' : plant ? 'Save Changes' : 'Add Plant'}</Button>
      </div>
    </Modal>
  );
}
