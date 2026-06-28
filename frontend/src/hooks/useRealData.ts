/**
 * Real astronomical data hooks for AstroLens AI.
 * All hooks talk to the FastAPI backend which in turn
 * queries NASA Exoplanet Archive, ExoFOP, MAST, and NASA Image API.
 */
import { useState, useEffect, useCallback } from 'react';

const API = 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TOICandidate {
  id: string;
  name: string;
  tic_id: string;
  toi_id: string;
  mission: string;
  period: number;
  depth: number;
  duration: number;
  ra: number;
  dec: number;
  tmag: number;
  teff: number;
  st_rad: number;
  st_mass: number;
  distance_pc: number;
  snr: number;
  confidence: number;
  status: string;
  disposition: string;
  comments: string;
  source: string;
  sectors?: string;
}

export interface ConfirmedPlanet {
  pl_name: string;
  hostname: string;
  period_days: number;
  radius_earth: number;
  mass_earth: number | null;
  eq_temp_k: number;
  semi_major_au: number;
  eccentricity: number;
  disc_year: number;
  disc_method: string;
  ra: number;
  dec: number;
  distance_pc: number;
  tmag: number;
  st_teff: number;
  st_rad: number;
  st_mass: number;
  source: string;
}

export interface LiveStats {
  total_confirmed: number;
  tess_confirmed: number;
  tess_candidates: number;
  habitable_zone?: number;
  current_sector: number;
  mission_progress: number;
  release_countdown_days: number;
  source?: string;
}

export interface NASAImage {
  nasa_id: string;
  title: string;
  description: string;
  date: string;
  center: string;
  credit: string;
  thumbnail: string;
  url: string;
}

export interface APODItem {
  title: string;
  explanation: string;
  date: string;
  url: string;
  hdurl: string;
  media_type: string;
  copyright: string;
}

export interface TICInfo {
  tic_id: number;
  ra?: number;
  dec?: number;
  Tmag?: number;
  Teff?: number;
  logg?: number;
  R_star?: number;
  M_star?: number;
  distance_pc?: number;
}

// ─── Generic fetch hook ───────────────────────────────────────────────────────

function useApiData<T>(
  url: string,
  initialData: T,
  deps: any[] = []
): { data: T; loading: boolean; error: string | null; refetch: () => void } {
  const [data, setData] = useState<T>(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(20000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setData(json);
    } catch (e: any) {
      setError(e.message || 'Network error');
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => { fetchData(); }, [fetchData, ...deps]);

  return { data, loading, error, refetch: fetchData };
}

// ─── Concrete Hooks ───────────────────────────────────────────────────────────

/** Real TESS Objects of Interest from ExoFOP/TFOPWG */
export function useTOICandidates(limit = 50) {
  const result = useApiData<{ candidates: TOICandidate[]; count: number; source: string }>(
    `${API}/api/tess/candidates?limit=${limit}`,
    { candidates: [], count: 0, source: '' },
    [limit]
  );
  return {
    candidates: result.data.candidates,
    count: result.data.count,
    source: result.data.source,
    loading: result.loading,
    error: result.error,
    refetch: result.refetch,
  };
}

/** Live mission stats: confirmed planet counts, sector, progress */
export function useLiveStats() {
  const result = useApiData<LiveStats>(
    `${API}/api/stats/live`,
    {
      total_confirmed: 5700, tess_confirmed: 480, tess_candidates: 7300,
      current_sector: 68, mission_progress: 0.94, release_countdown_days: 14,
    }
  );
  return { stats: result.data, loading: result.loading, error: result.error, refetch: result.refetch };
}

/** Confirmed exoplanets from NASA Exoplanet Archive TAP */
export function useConfirmedPlanets(limit = 100) {
  const result = useApiData<{ planets: ConfirmedPlanet[]; count: number; source: string }>(
    `${API}/api/exoplanets?limit=${limit}`,
    { planets: [], count: 0, source: '' },
    [limit]
  );
  return {
    planets: result.data.planets,
    count: result.data.count,
    source: result.data.source,
    loading: result.loading,
    error: result.error,
  };
}

/** NASA Image Library search */
export function useNASAImages(query: string, count = 12) {
  const result = useApiData<{ images: NASAImage[]; count: number; query: string }>(
    `${API}/api/nasa/images?query=${encodeURIComponent(query)}&count=${count}`,
    { images: [], count: 0, query },
    [query, count]
  );
  return {
    images: result.data.images,
    loading: result.loading,
    error: result.error,
  };
}

/** Curated multi-category NASA gallery */
export function useNASAGallery() {
  const result = useApiData<{ gallery: Record<string, NASAImage[]>; source: string }>(
    `${API}/api/nasa/gallery`,
    { gallery: {}, source: '' }
  );
  return {
    gallery: result.data.gallery,
    loading: result.loading,
    error: result.error,
    refetch: result.refetch,
  };
}

/** Astronomy Picture of the Day */
export function useAPOD(count = 3) {
  const result = useApiData<{ apod: APODItem[]; count: number }>(
    `${API}/api/nasa/apod?count=${count}`,
    { apod: [], count: 0 },
    [count]
  );
  return {
    apod: result.data.apod,
    latest: result.data.apod[0] ?? null,
    loading: result.loading,
    error: result.error,
  };
}

/** TIC stellar parameters from MAST */
export function useTICInfo(ticId: string | null) {
  const [info, setInfo] = useState<TICInfo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticId) return;
    const numId = ticId.replace(/\D/g, '');
    if (!numId) return;
    setLoading(true);
    fetch(`${API}/api/tess/tic/${numId}`)
      .then(r => r.json())
      .then(d => setInfo(d.stellar_params))
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [ticId]);

  return { info, loading };
}

/** Mission status (TESS current sector + MAST) */
export function useMissionStatus() {
  const result = useApiData<{
    current_sector: number; ongoing_observations: number;
    new_releases: number; release_countdown_days: number;
    mission_progress: number; source: string;
  }>(
    `${API}/api/mission/status`,
    { current_sector: 68, ongoing_observations: 200, new_releases: 47, release_countdown_days: 14, mission_progress: 0.94, source: '' }
  );
  return { status: result.data, loading: result.loading, error: result.error };
}
