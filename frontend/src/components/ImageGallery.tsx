/**
 * Image Gallery component — displays real NASA mission imagery.
 * Uses the NASA Image & Video Library API (no key required).
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Calendar, Building2, ImageIcon, RefreshCw } from 'lucide-react';
import { useNASAGallery, useAPOD } from '../hooks/useRealData';
import type { NASAImage, APODItem } from '../hooks/useRealData';

// Skeleton loader for images
function ImageSkeleton() {
  return (
    <div className="rounded-xl bg-white/3 border border-white/5 overflow-hidden animate-pulse">
      <div className="h-48 bg-white/5" />
      <div className="p-3 space-y-2">
        <div className="h-3 bg-white/5 rounded w-3/4" />
        <div className="h-2 bg-white/5 rounded w-1/2" />
      </div>
    </div>
  );
}

// Individual image card
function ImageCard({ img, onClick }: { img: NASAImage; onClick: () => void }) {
  const [loaded, setLoaded] = useState(false);
  const [errored, setErrored] = useState(false);

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      onClick={onClick}
      className="rounded-xl bg-white/3 border border-white/5 overflow-hidden cursor-pointer group hover:border-cyan-500/30 transition-all duration-300"
    >
      <div className="h-48 bg-[#080d1a] relative overflow-hidden">
        {!errored ? (
          <img
            src={img.thumbnail}
            alt={img.title}
            onLoad={() => setLoaded(true)}
            onError={() => setErrored(true)}
            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="h-10 w-10 text-gray-700" />
          </div>
        )}
        {!loaded && !errored && (
          <div className="absolute inset-0 bg-white/3 animate-pulse" />
        )}
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end p-3">
          <span className="text-[10px] text-cyan-300 font-medium">Click to expand →</span>
        </div>
      </div>
      <div className="p-3 space-y-1.5">
        <h4 className="text-xs font-bold text-gray-200 leading-tight line-clamp-2">{img.title}</h4>
        <div className="flex items-center space-x-3 text-[10px] text-gray-500">
          <span className="flex items-center space-x-1">
            <Calendar className="h-3 w-3" /><span>{img.date}</span>
          </span>
          <span className="flex items-center space-x-1">
            <Building2 className="h-3 w-3" /><span>{img.center || 'NASA'}</span>
          </span>
        </div>
        {img.credit && (
          <div className="text-[9px] text-gray-600 truncate">Credit: {img.credit}</div>
        )}
      </div>
    </motion.div>
  );
}

// Lightbox modal
function ImageLightbox({ img, onClose }: { img: NASAImage; onClose: () => void }) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-sm flex items-center justify-center p-6"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={e => e.stopPropagation()}
          className="max-w-3xl w-full bg-[#0a0f1e] border border-white/10 rounded-2xl overflow-hidden shadow-2xl"
        >
          <div className="relative">
            <img src={img.url} alt={img.title} className="w-full max-h-[60vh] object-cover" />
            <button onClick={onClose} className="absolute top-3 right-3 p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-all">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="p-6 space-y-3">
            <h3 className="text-lg font-bold text-white">{img.title}</h3>
            <p className="text-sm text-gray-400 leading-relaxed">{img.description}</p>
            <div className="flex items-center justify-between pt-2 border-t border-white/5">
              <div className="space-y-1">
                <div className="text-[10px] text-gray-500">
                  <span className="text-gray-400 font-medium">Date:</span> {img.date}
                </div>
                <div className="text-[10px] text-gray-500">
                  <span className="text-gray-400 font-medium">Credit:</span> {img.credit || 'NASA'}
                </div>
                <div className="text-[10px] text-gray-500">
                  <span className="text-gray-400 font-medium">Center:</span> {img.center || 'NASA'}
                </div>
                <div className="text-[10px] text-cyan-500">Source: NASA Image & Video Library</div>
              </div>
              <a href={img.hdurl || img.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center space-x-2 px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-lg text-xs text-cyan-300 font-medium transition-all">
                <ExternalLink className="h-3.5 w-3.5" /><span>Full Resolution</span>
              </a>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// APOD Card
function APODCard({ item }: { item: APODItem }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="rounded-xl bg-gradient-to-br from-purple-500/5 to-blue-500/5 border border-purple-500/20 overflow-hidden"
    >
      {item.media_type === 'image' && (
        <div className="h-52 overflow-hidden relative">
          <img src={item.url} alt={item.title} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
          <div className="absolute bottom-3 left-3 right-3">
            <h4 className="text-sm font-bold text-white leading-tight">{item.title}</h4>
            <div className="text-[10px] text-gray-300 mt-0.5">{item.date}</div>
          </div>
        </div>
      )}
      <div className="p-4 space-y-2">
        {item.media_type !== 'image' && <h4 className="text-sm font-bold text-gray-200">{item.title}</h4>}
        <p className={`text-xs text-gray-400 leading-relaxed ${expanded ? '' : 'line-clamp-3'}`}>
          {item.explanation}
        </p>
        <div className="flex items-center justify-between">
          <button onClick={() => setExpanded(p => !p)} className="text-[10px] text-cyan-400 hover:underline">
            {expanded ? 'Show less' : 'Read more'}
          </button>
          <div className="text-[9px] text-gray-600">© {item.copyright}</div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Main Gallery Component ───────────────────────────────────────────────────

export default function ImageGallery() {
  const { gallery, loading: galleryLoading, refetch } = useNASAGallery();
  const { apod, loading: apodLoading } = useAPOD(2);
  const [activeCategory, setActiveCategory] = useState<string>('');
  const [lightboxImg, setLightboxImg] = useState<NASAImage | null>(null);

  const categories = Object.keys(gallery);
  const currentCat = activeCategory || categories[0] || '';
  const currentImages = gallery[currentCat] || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Mission Image Gallery</h2>
          <p className="text-gray-500 text-sm mt-0.5">
            Real NASA mission imagery — TESS, exoplanets, nebulae & galaxies
          </p>
        </div>
        <button
          onClick={refetch}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-white/3 border border-white/5 text-xs text-gray-400 hover:text-white transition-all"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${galleryLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* APOD Section */}
      {!apodLoading && apod.length > 0 && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3 flex items-center space-x-2">
            <span className="h-1.5 w-1.5 rounded-full bg-purple-400 animate-pulse inline-block" />
            <span>Astronomy Picture of the Day — NASA APOD</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {apod.slice(0, 2).map((item, i) => <APODCard key={i} item={item} />)}
          </div>
        </div>
      )}

      {/* Category Tabs */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all ${currentCat === cat ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-300' : 'bg-white/3 border border-white/5 text-gray-500 hover:text-gray-200 hover:border-white/10'}`}
            >
              {cat}
              {gallery[cat] && <span className="ml-1.5 text-[9px] opacity-60">{gallery[cat].length}</span>}
            </button>
          ))}
        </div>
      )}

      {/* Image Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {galleryLoading
          ? Array.from({ length: 8 }).map((_, i) => <ImageSkeleton key={i} />)
          : currentImages.map((img, i) => (
              <ImageCard key={img.nasa_id || i} img={img} onClick={() => setLightboxImg(img)} />
            ))
        }
        {!galleryLoading && currentImages.length === 0 && (
          <div className="col-span-4 py-16 text-center text-gray-600 text-sm">
            <ImageIcon className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No images found for this category</p>
          </div>
        )}
      </div>

      {/* Attribution */}
      <div className="p-4 rounded-xl bg-white/2 border border-white/5 text-[10px] text-gray-600 flex items-center justify-between">
        <span>All images from NASA Image & Video Library — <span className="text-cyan-600">images.nasa.gov</span></span>
        <span>Public domain · NASA/JPL-Caltech/STScI</span>
      </div>

      {/* Lightbox */}
      {lightboxImg && <ImageLightbox img={lightboxImg} onClose={() => setLightboxImg(null)} />}
    </div>
  );
}
