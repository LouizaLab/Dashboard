// Configuration for Market Preference Manifold labels and event markers
// Coordinates are in normalized space (-1 to 1) for the manifold surface

export interface SurfaceLabel {
  text: string;
  position: [number, number]; // [x, z] in normalized coordinates
}

export interface EventMarker {
  id: string;
  label: string;
  position: [number, number]; // [x, z] in normalized coordinates
  icon: 'downturn' | 'viral' | 'regulation';
  impactColor: string; // '#ff3b3b' for red, '#3bff7a' for green
  arrowDirection: 'up' | 'down';
}

export interface AxisConfig {
  label: string;
  direction: [number, number, number]; // Direction vector
  position: [number, number, number]; // Base position
}

export const SURFACE_LABELS: SurfaceLabel[] = [
  { text: 'Frugality Surge', position: [-0.7, -0.6] },
  { text: 'Loyalty Dip', position: [-0.5, -0.3] },
  { text: 'Excitement Boost', position: [0.1, -0.2] },
  { text: 'Hype Spike', position: [0.0, 0.0] },
  { text: 'Eco Shift', position: [0.5, 0.3] },
];

export const EVENT_MARKERS: EventMarker[] = [
  {
    id: 'economic-downturn',
    label: 'Economic Downturn',
    position: [-0.7, -0.6],
    icon: 'downturn',
    impactColor: '#ff3b3b',
    arrowDirection: 'down',
  },
  {
    id: 'viral-trend',
    label: 'Viral Trend',
    position: [0.0, 0.0],
    icon: 'viral',
    impactColor: '#3bff7a',
    arrowDirection: 'up',
  },
  {
    id: 'regulation-change',
    label: 'Regulation Change',
    position: [0.5, 0.3],
    icon: 'regulation',
    impactColor: '#3bff7a',
    arrowDirection: 'up',
  },
];

export const AXES: AxisConfig[] = [
  {
    label: 'Price Sensitivity',
    direction: [-0.7, 0, -0.7],
    position: [0, -0.3, 0],
  },
  {
    label: 'Brand Loyalty',
    direction: [0.7, 0, -0.7],
    position: [0, -0.3, 0],
  },
  {
    label: 'Trend Fit',
    direction: [0, 1, 0],
    position: [-0.5, -0.3, 0],
  },
];

// Manifold dimensions
export const MANIFOLD_SIZE = 4; // Size of the manifold plane
export const MANIFOLD_SEGMENTS = 200; // Grid resolution
