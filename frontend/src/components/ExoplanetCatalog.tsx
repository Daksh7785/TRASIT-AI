/**
 * Exoplanet Catalog — confirmed planets from NASA Exoplanet Archive.
 * Searchable, sortable, with real physical parameters.
 */
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Globe, ArrowUpDown, ExternalLink, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { useConfirmedPlanets } from '../hooks/useRealData';
import type { ConfirmedPlanet } from '../hooks/useRealData';

type SortKey = 'pl_name' | 'period_days' | 'radius_earth' | 'disc_year' | 'eq_temp_k' | 'distance_pc';

function spectralColor(teff: number): string {
  if (teff > 7500) return 'text-blue-300';
  if (teff > 6000) return 'text-yellow-200';
  if (teff > 5000) return 'text-amber-300';
  if (teff > 3500) return 'text-orange-400';
  return 'text-red-400';
}

function spectralType(teff: number): string {
  if (teff > 30000) return 'O';
  if (teff > 10000) return 'B';
  if (teff > 7500)  return 'A';
  if (teff > 6000)  return 'F';
  if (teff > 5200)  return 'G';
  if (teff > 3700)  return 'K';
  return 'M';
}

function habitabilityBadge(planet: ConfirmedPlanet): { label: string; cls: string } | null {
  const { eq_temp_k, radius_earth } = planet;
  if (eq_temp_k && eq_temp_k >= 200 && eq_temp_k <= 320 && radius_earth && radius_earth < 2) {
    return { label: 'HZ', cls: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' };
  }
  return null;
}

// ─── Row Component ─────────────────────────────────────────────────────────────

function PlanetRow({ planet, idx }: { planet: ConfirmedPlanet; idx: number }) {
  const [expanded, setExpanded] = useState(false);
  const hzBadge = habitabilityBadge(planet);

  return (
    <>
      <motion.tr
        whileHover={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
        onClick={() => setExpanded(p => !p)}
        className="border-b border-white/3 cursor-pointer transition-all"
      >
        <td className="py-3 px-4 text-xs text-gray-500 font-mono w-10">{idx + 1}</td>
        <td className="py-3 px-4">
          <div className="flex items-center space-x-2">
            <div className="text-sm font-bold text-gray-100">{planet.pl_name}</div>
            {hzBadge && (
              <span className={`text-[9px] px-1.5 py-0.5 rounded border font-bold ${hzBadge.cls}`}>{hzBadge.label}</span>
            )}
          </div>
          <div className="text-[10px] text-gray-500">{planet.hostname}</div>
        </td>
        <td className="py-3 px-4">
          <span className={`text-xs font-bold ${spectralColor(planet.st_teff)}`}>
            {spectralType(planet.st_teff)}-type
          </span>
          <div className="text-[10px] text-gray-500">{planet.st_teff ? `${planet.st_teff.toFixed(0)} K` : '—'}</div>
        </td>
        <td className="py-3 px-4 text-xs text-gray-300 font-mono">
          {planet.period_days ? planet.period_days.toFixed(3) + 'd' : '—'}
        </td>
        <td className="py-3 px-4 text-xs text-gray-300 font-mono">
          {planet.radius_earth ? planet.radius_earth.toFixed(2) + ' R⊕' : '—'}
        </td>
        <td className="py-3 px-4 text-xs text-gray-300 font-mono">
          {planet.eq_temp_k ? planet.eq_temp_k.toFixed(0) + ' K' : '—'}
        </td>
        <td className="py-3 px-4 text-xs text-gray-400">
          {planet.distance_pc ? `${planet.distance_pc.toFixed(1)} pc` : '—'}
        </td>
        <td className="py-3 px-4">
          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${
            planet.disc_method?.includes('Transit') ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20'
            : 'bg-purple-500/10 text-purple-300 border-purple-500/20'
          }`}>
            {planet.disc_method?.replace('Radial Velocity', 'RV') || '—'}
          </span>
        </td>
        <td className="py-3 px-4 text-xs text-gray-500">{planet.disc_year || '—'}</td>
      </motion.tr>

      {/* Expanded row */}
      {expanded && (
        <tr className="border-b border-white/3">
          <td colSpan={9} className="px-4 py-4 bg-white/2">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { l: 'RA / Dec', v: planet.ra ? `${planet.ra.toFixed(3)}° / ${planet.dec.toFixed(3)}°` : '—' },
                { l: 'Semi-major axis', v: planet.semi_major_au ? `${planet.semi_major_au.toFixed(3)} AU` : '—' },
                { l: 'Eccentricity', v: planet.eccentricity != null ? planet.eccentricity.toFixed(4) : '—' },
                { l: 'Planet mass', v: planet.mass_earth ? `${planet.mass_earth.toFixed(2)} M⊕` : '—' },
                { l: 'Star radius', v: planet.st_rad ? `${planet.st_rad.toFixed(2)} R☉` : '—' },
                { l: 'Star mass', v: planet.st_mass ? `${planet.st_mass.toFixed(2)} M☉` : '—' },
                { l: 'Host star', v: planet.hostname },
                { l: 'Data source', v: planet.source || 'NASA Exoplanet Archive' },
              ].map((p, i) => (
                <div key={i} className="text-xs">
                  <div className="text-gray-500 mb-0.5">{p.l}</div>
                  <div className="text-gray-200 font-semibold">{p.v}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center space-x-3">
              <a
                href={`https://exoplanetarchive.ipac.caltech.edu/overview/${encodeURIComponent(planet.pl_name)}`}
                target="_blank" rel="noopener noreferrer"
                className="flex items-center space-x-1.5 text-[10px] text-cyan-400 hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                <span>NASA Exoplanet Archive</span>
              </a>
              <a
                href={`https://simbad.u-strasbg.fr/simbad/sim-id?Ident=${encodeURIComponent(planet.hostname)}`}
                target="_blank" rel="noopener noreferrer"
                className="flex items-center space-x-1.5 text-[10px] text-purple-400 hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                <span>SIMBAD</span>
              </a>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ─── Main Catalog Component ────────────────────────────────────────────────────

export default function ExoplanetCatalog() {
  const { planets, count, source, loading } = useConfirmedPlanets(150);
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('disc_year');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [methodFilter, setMethodFilter] = useState<string>('all');
  const [limitDisplay, setLimitDisplay] = useState(50);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const methods = useMemo(() => {
    const m = new Set(planets.map(p => p.disc_method).filter(Boolean));
    return ['all', ...Array.from(m)];
  }, [planets]);

  const filtered = useMemo(() => {
    let list = planets;
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(p =>
        p.pl_name?.toLowerCase().includes(q) ||
        p.hostname?.toLowerCase().includes(q) ||
        p.disc_method?.toLowerCase().includes(q)
      );
    }
    if (methodFilter !== 'all') {
      list = list.filter(p => p.disc_method === methodFilter);
    }
    list = [...list].sort((a, b) => {
      const va = (a[sortKey] as any) ?? 0;
      const vb = (b[sortKey] as any) ?? 0;
      if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb as string) : (vb as string).localeCompare(va);
      return sortDir === 'asc' ? (va as number) - (vb as number) : (vb as number) - (va as number);
    });
    return list;
  }, [planets, search, sortKey, sortDir, methodFilter]);

  const displayed = filtered.slice(0, limitDisplay);

  const SortBtn = ({ col, label }: { col: SortKey; label: string }) => (
    <button onClick={() => handleSort(col)} className="flex items-center space-x-1 hover:text-gray-200 transition-colors">
      <span>{label}</span>
      <ArrowUpDown className={`h-3 w-3 ${sortKey === col ? 'text-cyan-400' : 'text-gray-600'}`} />
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Confirmed Exoplanet Catalog</h2>
          <p className="text-gray-500 text-sm mt-0.5">
            {loading ? 'Loading...' : `${count} planets · `}
            <span className="text-cyan-600">{source || 'NASA Exoplanet Archive'}</span>
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-600" />
            <input
              type="text"
              placeholder="Search planet or host star..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-white/3 border border-white/10 rounded-lg text-xs text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/30 w-56"
            />
          </div>
          <div className="flex items-center space-x-2">
            <SlidersHorizontal className="h-3.5 w-3.5 text-gray-500" />
            <select
              value={methodFilter}
              onChange={e => setMethodFilter(e.target.value)}
              className="bg-white/3 border border-white/10 rounded-lg text-xs text-gray-300 px-3 py-2 focus:outline-none cursor-pointer"
            >
              {methods.map(m => (
                <option key={m} value={m} className="bg-[#0a0f1e]">{m === 'all' ? 'All methods' : m}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { l: 'Showing', v: `${displayed.length} / ${filtered.length}`, c: 'text-cyan-400' },
          { l: 'Transit discoveries', v: planets.filter(p => p.disc_method?.includes('Transit')).length, c: 'text-emerald-400' },
          { l: 'HZ candidates', v: planets.filter(p => habitabilityBadge(p) !== null).length, c: 'text-amber-400' },
          { l: 'Avg period', v: planets.length ? `${(planets.reduce((a, p) => a + (p.period_days || 0), 0) / planets.length).toFixed(1)}d` : '—', c: 'text-purple-400' },
        ].map((s, i) => (
          <div key={i} className="p-3 rounded-xl bg-white/3 border border-white/5 flex justify-between items-center">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">{s.l}</span>
            <span className={`text-sm font-bold ${s.c}`}>{s.v}</span>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/5 overflow-hidden bg-white/2 backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 bg-white/3">
                <th className="py-3 px-4 text-[10px] text-gray-600 font-bold w-10">#</th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="pl_name" label="Planet / Host" />
                </th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">Stellar Type</th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="period_days" label="Period" />
                </th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="radius_earth" label="Radius" />
                </th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="eq_temp_k" label="Teq (K)" />
                </th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="distance_pc" label="Distance" />
                </th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">Method</th>
                <th className="py-3 px-4 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  <SortBtn col="disc_year" label="Year" />
                </th>
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i} className="border-b border-white/3">
                      {Array.from({ length: 9 }).map((_, j) => (
                        <td key={j} className="py-3.5 px-4">
                          <div className="h-3 bg-white/5 rounded animate-pulse w-20" />
                        </td>
                      ))}
                    </tr>
                  ))
                : displayed.map((p, i) => <PlanetRow key={p.pl_name} planet={p} idx={i} />)
              }
            </tbody>
          </table>
        </div>

        {!loading && filtered.length > limitDisplay && (
          <div className="p-4 text-center border-t border-white/5">
            <button
              onClick={() => setLimitDisplay(n => n + 50)}
              className="px-6 py-2 bg-white/3 hover:bg-white/5 border border-white/10 rounded-lg text-xs text-gray-400 hover:text-white transition-all"
            >
              Load {Math.min(50, filtered.length - limitDisplay)} more planets
            </button>
          </div>
        )}
      </div>

      {/* Attribution */}
      <div className="p-3 rounded-xl bg-white/2 border border-white/5 text-[10px] text-gray-600 flex items-center justify-between">
        <span>Data: NASA Exoplanet Archive TAP Service · <span className="text-cyan-600">exoplanetarchive.ipac.caltech.edu</span></span>
        <a href="https://exoplanetarchive.ipac.caltech.edu" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1 text-cyan-600 hover:underline">
          <ExternalLink className="h-3 w-3" /><span>Open Archive</span>
        </a>
      </div>
    </div>
  );
}
