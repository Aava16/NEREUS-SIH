/**
 * Safe local storage management for NEREUS Snapshots and Annotations.
 */

import type { ScientificSnapshot, ScientificAnnotation } from '../types';

const SNAPSHOTS_KEY = 'nereus_scientific_snapshots';
const ANNOTATIONS_KEY = 'nereus_scientific_annotations';

// ================= SNAPSHOTS =================

export const loadSnapshots = (): ScientificSnapshot[] => {
  try {
    const raw = localStorage.getItem(SNAPSHOTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const saveSnapshot = (snapshot: ScientificSnapshot): ScientificSnapshot[] => {
  try {
    const current = loadSnapshots();
    const existingIndex = current.findIndex((s) => s.id === snapshot.id);
    let updated: ScientificSnapshot[];
    if (existingIndex >= 0) {
      updated = [...current];
      updated[existingIndex] = snapshot;
    } else {
      updated = [snapshot, ...current];
    }
    localStorage.setItem(SNAPSHOTS_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
};

export const deleteSnapshot = (id: string): ScientificSnapshot[] => {
  try {
    const current = loadSnapshots();
    const updated = current.filter((s) => s.id !== id);
    localStorage.setItem(SNAPSHOTS_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
};

export const renameSnapshot = (id: string, newName: string): ScientificSnapshot[] => {
  try {
    const current = loadSnapshots();
    const updated = current.map((s) => (s.id === id ? { ...s, name: newName } : s));
    localStorage.setItem(SNAPSHOTS_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
};

// ================= ANNOTATIONS =================

export const loadAnnotations = (): ScientificAnnotation[] => {
  try {
    const raw = localStorage.getItem(ANNOTATIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const saveAnnotation = (annotation: ScientificAnnotation): ScientificAnnotation[] => {
  try {
    const current = loadAnnotations();
    const existingIndex = current.findIndex((a) => a.id === annotation.id);
    let updated: ScientificAnnotation[];
    if (existingIndex >= 0) {
      updated = [...current];
      updated[existingIndex] = { ...annotation, updatedAt: new Date().toISOString() };
    } else {
      updated = [annotation, ...current];
    }
    localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
};

export const deleteAnnotation = (id: string): ScientificAnnotation[] => {
  try {
    const current = loadAnnotations();
    const updated = current.filter((a) => a.id !== id);
    localStorage.setItem(ANNOTATIONS_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
};
