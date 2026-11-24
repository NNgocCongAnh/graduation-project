import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Camera, Sparkles, ShieldCheck } from 'lucide-react';

export default function EvidenceSingleModal({ evidence, index, onClose, onZoomImage }) {
  if (!evidence) return null;

  let photoUrl = '/assets/evidence_glass.png';
  if (evidence.item_name.toLowerCase().includes('trà') || evidence.item_name.toLowerCase().includes('tách')) {
    photoUrl = '/assets/evidence_teacup.png';
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-950/85 backdrop-blur-md font-mono select-none overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative max-w-2xl w-full bg-[#f4ecd8] text-stone-900 rounded-sm p-6 sm:p-8 border-4 border-[#8c6b43] shadow-2xl overflow-hidden font-serif my-8"
          style={{
            backgroundImage: `radial-gradient(#e2d7c0 1px, transparent 1px)`,
            backgroundSize: '18px 18px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.85)'
          }}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-full bg-stone-900 text-amber-100 hover:bg-red-800 transition z-50"
          >
            <X size={20} />
          </button>

          {/* Header */}
          <div className="border-b-2 border-stone-800 pb-3 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-[10px] font-sans font-bold uppercase tracking-widest bg-stone-900 text-amber-300 px-2 py-0.5 rounded">
                PHIẾU PHÂN TÍCH TANG VẬT #EV-0{evidence.id || index + 1}
              </span>
              <h2 className="text-2xl font-bold font-mono text-stone-900 mt-1">{evidence.item_name}</h2>
            </div>
            {evidence.is_key_evidence && (
              <span className="bg-red-700 text-white font-sans text-xs uppercase tracking-wider font-bold px-2 py-1 rounded shadow">
                ★ TANG VẬT MẤU CHỐT
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-6">
            {/* Left Photo Polaroid */}
            <div className="sm:col-span-5 bg-white p-2 border-2 border-stone-400 shadow-md flex flex-col items-center group">
              <div 
                onClick={() => onZoomImage(photoUrl, evidence.item_name)}
                className="w-full h-44 bg-stone-950 overflow-hidden relative border border-stone-400 cursor-pointer"
              >
                <img
                  src={photoUrl}
                  alt={evidence.item_name}
                  className="w-full h-full object-cover grayscale contrast-125 group-hover:scale-105 transition duration-300"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <span className="text-[11px] text-white bg-black/80 px-2 py-1 rounded border border-amber-500/50 font-sans">
                    🔍 Click phóng to ảnh
                  </span>
                </div>
              </div>
              <div className="mt-2 text-center text-[11px] font-typewriter font-bold text-stone-800 tracking-wider">
                EVIDENCE ID: #EV-0{evidence.id || index + 1}
              </div>
            </div>

            {/* Right Details */}
            <div className="sm:col-span-7 space-y-4 font-mono text-xs">
              <div className="bg-amber-100/90 p-3 rounded border border-amber-300">
                <strong className="text-amber-900 font-sans block text-xs font-bold uppercase tracking-wider mb-1">
                  📍 Vị trí phát hiện hiện trường:
                </strong>
                <p className="text-stone-900 font-bold">{evidence.location_found || 'Hiện trường vụ án'}</p>
              </div>

              <div className="bg-[#fffdf7] p-3 rounded border border-stone-300 leading-relaxed shadow-xs">
                <strong className="text-stone-900 font-sans block text-xs font-bold uppercase tracking-wider mb-1">
                  🔬 Báo cáo phân tích đường vân & hóa nghiệm:
                </strong>
                <p className="text-stone-800">{evidence.description}</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-stone-400 flex items-center justify-between font-sans">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-stone-800 hover:bg-stone-900 text-white rounded text-xs font-bold transition"
            >
              Đóng phiếu tang vật
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
