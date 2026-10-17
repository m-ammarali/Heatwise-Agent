import type { LocationIn } from "../types/api";

// Three Lahore sites verified against live OpenStreetMap land cover (probe results):
// a dense bazaar, a large park and a stadium surrounding. Same weather grid cell,
// very different surroundings - which is what HeatWise is built to show.
export const LAHORE_DEMO_SCENARIO: LocationIn[] = [
  { name: "Anarkali Bazaar", latitude: 31.5667, longitude: 74.3097 },
  { name: "Bagh-e-Jinnah", latitude: 31.5537, longitude: 74.3313 },
  { name: "Gaddafi Stadium", latitude: 31.5133, longitude: 74.3333 },
];

export const PHOENIX_DEMO_SCENARIO: LocationIn[] = [
  { name: "Phoenix Construction Zone", latitude: 33.4484, longitude: -112.0740 },
  { name: "Scottsdale Work Area", latitude: 33.4942, longitude: -111.9261 },
  { name: "Papago Park Delivery Hub", latitude: 33.4600, longitude: -111.9470 },
];
