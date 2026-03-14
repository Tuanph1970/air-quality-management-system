import { useState } from 'react';
import PropTypes from 'prop-types';
import { MapPin, RotateCcw } from 'lucide-react';
import Modal from './Modal';
import useLocationStore, { DEFAULT_LOCATION } from '../../store/locationStore';

function Field({ label, hint, name, value, onChange, min, max, step = '0.0001' }) {
  return (
    <div>
      <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">
        {label}
        {hint && <span className="ml-1 text-[var(--color-text-muted)] font-normal">{hint}</span>}
      </label>
      <input
        type="number"
        name={name}
        value={value}
        onChange={onChange}
        step={step}
        min={min}
        max={max}
        className="w-full bg-white/5 border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm
                   text-[var(--color-text-primary)] font-mono
                   focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30
                   transition-colors"
      />
    </div>
  );
}

Field.propTypes = {
  label: PropTypes.string.isRequired,
  hint: PropTypes.string,
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  min: PropTypes.string,
  max: PropTypes.string,
  step: PropTypes.string,
};

function LocationSettingsDialog({ isOpen, onClose }) {
  const location = useLocationStore();
  const [form, setForm] = useState({
    label: location.label,
    latitude: location.latitude,
    longitude: location.longitude,
    bboxNorth: location.bboxNorth,
    bboxSouth: location.bboxSouth,
    bboxEast: location.bboxEast,
    bboxWest: location.bboxWest,
  });
  const [saved, setSaved] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === 'label' ? value : parseFloat(value) || 0,
    }));
    setSaved(false);
  }

  function handleSave() {
    location.update(form);
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  }

  function handleReset() {
    const d = DEFAULT_LOCATION;
    setForm({
      label: d.label,
      latitude: d.latitude,
      longitude: d.longitude,
      bboxNorth: d.bboxNorth,
      bboxSouth: d.bboxSouth,
      bboxEast: d.bboxEast,
      bboxWest: d.bboxWest,
    });
    setSaved(false);
  }

  const isValid =
    form.latitude >= -90 && form.latitude <= 90 &&
    form.longitude >= -180 && form.longitude <= 180 &&
    form.bboxNorth > form.bboxSouth &&
    form.bboxEast > form.bboxWest;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Location &amp; Region Settings"
      size="md"
      footer={
        <>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-[var(--color-text-muted)]
                       hover:text-[var(--color-text-primary)] hover:bg-white/5 rounded-lg transition-colors mr-auto"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to defaults
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs rounded-lg border border-[var(--color-border)]
                       text-[var(--color-text-secondary)] hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!isValid}
            className="px-4 py-1.5 text-xs rounded-lg bg-brand-600 hover:bg-brand-500
                       text-white font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saved ? 'Saved ✓' : 'Save'}
          </button>
        </>
      }
    >
      <div className="space-y-5">
        {/* Label */}
        <div>
          <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">
            Region name
          </label>
          <input
            type="text"
            name="label"
            value={form.label}
            onChange={handleChange}
            placeholder="e.g. Hanoi, Vietnam"
            className="w-full bg-white/5 border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm
                       text-[var(--color-text-primary)]
                       focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30
                       transition-colors"
          />
        </div>

        {/* Center point */}
        <div>
          <p className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-text-primary)] mb-3">
            <MapPin className="w-3.5 h-3.5 text-brand-400" />
            City center
            <span className="font-normal text-[var(--color-text-muted)]">— used for current AQI queries</span>
          </p>
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Latitude" hint="−90 … 90"
              name="latitude" value={form.latitude}
              onChange={handleChange} min="-90" max="90"
            />
            <Field
              label="Longitude" hint="−180 … 180"
              name="longitude" value={form.longitude}
              onChange={handleChange} min="-180" max="180"
            />
          </div>
        </div>

        {/* Bounding box */}
        <div>
          <p className="text-xs font-semibold text-[var(--color-text-primary)] mb-1">
            Bounding box
            <span className="ml-1 font-normal text-[var(--color-text-muted)]">— used for map &amp; heatmap queries</span>
          </p>
          {!isValid && form.bboxNorth <= form.bboxSouth && (
            <p className="text-xs text-red-400 mb-2">North must be greater than South.</p>
          )}
          {!isValid && form.bboxEast <= form.bboxWest && (
            <p className="text-xs text-red-400 mb-2">East must be greater than West.</p>
          )}

          {/* Visual bbox diagram */}
          <div className="relative border border-dashed border-[var(--color-border)] rounded-xl p-4 mb-3 bg-white/[0.02]">
            <div className="flex justify-center mb-2">
              <Field
                label="North" name="bboxNorth" value={form.bboxNorth}
                onChange={handleChange} min="-90" max="90"
              />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <Field
                  label="West" name="bboxWest" value={form.bboxWest}
                  onChange={handleChange} min="-180" max="180"
                />
              </div>
              <div className="w-10 h-10 flex-shrink-0 rounded-lg border border-[var(--color-border)] bg-brand-600/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-brand-400" />
              </div>
              <div className="flex-1">
                <Field
                  label="East" name="bboxEast" value={form.bboxEast}
                  onChange={handleChange} min="-180" max="180"
                />
              </div>
            </div>
            <div className="flex justify-center mt-2">
              <Field
                label="South" name="bboxSouth" value={form.bboxSouth}
                onChange={handleChange} min="-90" max="90"
              />
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}

LocationSettingsDialog.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default LocationSettingsDialog;
