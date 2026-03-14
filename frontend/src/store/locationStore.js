import { create } from 'zustand';

const STORAGE_KEY = 'aqms_location_settings';

const DEFAULT_LOCATION = {
  // City center — used for getCurrentAqi, getForecast, getHistory
  latitude: 21.0285,
  longitude: 105.8542,
  // Bounding box — used for getMapData and heatmap tiles
  bboxNorth: 21.1,
  bboxSouth: 20.9,
  bboxEast: 105.95,
  bboxWest: 105.75,
  label: 'Hanoi, Vietnam',
};

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? { ...DEFAULT_LOCATION, ...JSON.parse(raw) } : DEFAULT_LOCATION;
  } catch {
    return DEFAULT_LOCATION;
  }
}

const useLocationStore = create((set, get) => ({
  ...loadFromStorage(),

  update: (fields) => {
    set(fields);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...get(), ...fields }));
    } catch {
      // ignore storage errors
    }
  },

  reset: () => {
    set(DEFAULT_LOCATION);
    localStorage.removeItem(STORAGE_KEY);
  },
}));

export { DEFAULT_LOCATION };
export default useLocationStore;
