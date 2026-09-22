/**
 * Scientific perceptually-uniform and oceanographic colormaps.
 * Includes cmocean-inspired palettes (thermal, haline, coolwarm) and standard perceptually-linear scales (viridis, plasma, turbo).
 */

import type { ColormapName } from "../types";

export type { ColormapName };

export const COLORMAP_NAMES: ColormapName[] = [
  "viridis",
  "plasma",
  "thermal",
  "haline",
  "coolwarm",
  "turbo",
];

export type RGB = [number, number, number];
export type RGBA = [number, number, number, number];

// Colormap lookup keypoints: [normalized_pos, [r, g, b]]
const COLORMAP_STOPS: Record<ColormapName, Array<[number, RGB]>> = {
  viridis: [
    [0.0, [68, 1, 84]],
    [0.25, [59, 82, 139]],
    [0.5, [33, 145, 140]],
    [0.75, [94, 201, 98]],
    [1.0, [253, 231, 37]],
  ],
  plasma: [
    [0.0, [13, 8, 135]],
    [0.25, [126, 3, 168]],
    [0.5, [204, 71, 120]],
    [0.75, [248, 149, 64]],
    [1.0, [240, 249, 33]],
  ],
  thermal: [
    // Ocean Temperature: Deep indigo -> blue -> cyan -> gold -> bright yellow
    [0.0, [4, 5, 25]],
    [0.2, [20, 50, 110]],
    [0.4, [30, 130, 160]],
    [0.6, [220, 120, 50]],
    [0.8, [245, 190, 40]],
    [1.0, [255, 250, 200]],
  ],
  haline: [
    // Ocean Salinity: Deep blue-green -> emerald -> warm ochre -> sand
    [0.0, [15, 30, 60]],
    [0.25, [20, 100, 100]],
    [0.5, [70, 170, 120]],
    [0.75, [200, 190, 90]],
    [1.0, [245, 235, 190]],
  ],
  coolwarm: [
    // Diverging: Cool Deep Blue -> Neutral White -> Warm Red
    [0.0, [59, 76, 192]],
    [0.25, [124, 159, 248]],
    [0.5, [221, 221, 221]],
    [0.75, [244, 109, 85]],
    [1.0, [180, 4, 38]],
  ],
  turbo: [
    [0.0, [48, 18, 59]],
    [0.25, [33, 145, 240]],
    [0.5, [90, 215, 60]],
    [0.75, [240, 180, 20]],
    [1.0, [160, 20, 10]],
  ],
};

function interpolateRGB(c1: RGB, c2: RGB, factor: number): RGB {
  const f = Math.max(0, Math.min(1, factor));
  return [
    Math.round(c1[0] + (c2[0] - c1[0]) * f),
    Math.round(c1[1] + (c2[1] - c1[1]) * f),
    Math.round(c1[2] + (c2[2] - c1[2]) * f),
  ];
}

/**
 * Get RGB tuple [r, g, b] for normalized value in [0, 1].
 */
export function getRGBForNormalizedValue(val: number, colormap: ColormapName): RGB {
  const stops = COLORMAP_STOPS[colormap] || COLORMAP_STOPS.viridis;
  const clamped = Math.max(0, Math.min(1, val));

  for (let i = 0; i < stops.length - 1; i++) {
    const [pos1, rgb1] = stops[i];
    const [pos2, rgb2] = stops[i + 1];

    if (clamped >= pos1 && clamped <= pos2) {
      const localFactor = (clamped - pos1) / (pos2 - pos1);
      return interpolateRGB(rgb1, rgb2, localFactor);
    }
  }

  return stops[stops.length - 1][1];
}

/**
 * Get RGBA tuple [r, g, b, a] for normalized value in [0, 1].
 */
export function getColorRgba(val: number, colormap: ColormapName, alpha: number = 1.0): RGBA {
  const [r, g, b] = getRGBForNormalizedValue(val, colormap);
  return [r, g, b, alpha];
}

/**
 * Get Hex string #RRGGBB for normalized value in [0, 1].
 */
export function getColorHex(val: number, colormap: ColormapName): string {
  const [r, g, b] = getRGBForNormalizedValue(val, colormap);
  const toHex = (n: number) => n.toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Get CSS color string (rgb or rgba) for numerical value against min/max bounds.
 */
export function getColorForValue(
  val: number | null | undefined,
  min: number,
  max: number,
  colormap: ColormapName = "viridis",
  nanColor: string = "rgba(30, 41, 59, 0.4)"
): string {
  if (val === null || val === undefined || isNaN(val) || !isFinite(val)) {
    return nanColor;
  }

  const range = max - min;
  const norm = range === 0 ? 0.5 : (val - min) / range;
  const [r, g, b] = getRGBForNormalizedValue(norm, colormap);
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Generate CSS linear-gradient string for a colormap colorbar.
 */
export function getColormapGradientCSS(colormap: ColormapName): string {
  const stops = COLORMAP_STOPS[colormap] || COLORMAP_STOPS.viridis;
  const parts = stops.map(([pos, [r, g, b]]) => `rgb(${r}, ${g}, ${b}) ${pos * 100}%`);
  return `linear-gradient(to right, ${parts.join(", ")})`;
}
