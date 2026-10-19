import React from 'react';
import { motion } from 'framer-motion';
import { Pin, Camera, ShieldAlert, Sparkles } from 'lucide-react';

export default function EvidenceCard({ evidence, index, isSelected, onPinClick, onOpenDetail }) {
  const cardId = `evidence-${evidence.id || index + 1}`;

  // Map photo assets
  let photoUrl = '/assets/evidence_glass.png';
  if (evidence.item_name.toLowerCase().includes('trà') || evidence.item_name.toLowerCase().includes('tách')) {
    photoUrl = '/assets/evidence_teacup.png';
  } else if (evidence.item_name.toLowerCase().includes('chỉ') || evidence.item_name.toLowerCase().includes('áo')) {
    photoUrl = '/assets/evidence_glass.png';
  }

  return (
    <motion.div
      initial={{ rotate: index % 2 === 0 ? -2 : 2, y: 10, opacity: 0 }}
      animate={{ rotate: index % 2 === 0 ? -2 : 2, y: 0, opacity: 1 }}
      whileHover={{ scale: 1.04, rotate: 0, zIndex: 30 }}
      className={`relative w-60 p-3 rounded-xs border-2 shadow-2xl font-mono flex flex-col justify-between cursor-pointer select-none group ${
        evidence.is_key_evidence
          ? 'bg-[#f4ebd0] border-amber-800'
          : 'bg-[#ede7d5] border-stone-400'
      }`}
      style={{
        boxShadow: '8px 12px 24px rgba(0,0,0,0.6)'
      }}
      onClick={() => onOpenDetail(evidence)}
    >
      {/* Red Thumbtack Pin Button */}
      <button
        id={`pin-${cardId}`}
        onClick={(e) => {
          e.stopPropagation();
          onPinClick(e, { id: cardId, name: evidence.item_name });
        }}
        className={`absolute -top-3.5 right-4 w-6 h-6 rounded-full flex items-center justify-center transition shadow-xl z-40 ${
          isSelected 
            ? 'bg-amber-400 ring-4 ring-amber-300 scale-125' 
            : 'bg-red-600 hover:bg-red-500 hover:scale-110'
        }`}
        title={`Nối dây chỉ đỏ cho chứng cứ ${evidence.item_name}`}
      >
        <Pin size={12} className="text-white transform -rotate-45" />
      </button>

      <div>
        {/* Header Tag */}
        <div className="flex items-center justify-between border-b border-stone-400 pb-1 mb-2 text-[10px] font-sans">
          <span className="font-bold text-amber-900 uppercase flex items-center gap-1">
            <Camera size={12} /> TANG VẬT #{index + 1}
          </span>
          {evidence.is_key_evidence && (
            <span className="bg-red-700 text-white font-bold px-1.5 py-0.2 rounded text-[9px] uppercase tracking-wider">
              ★ MẤU CHỐT
            </span>
          )}
        </div>

        {/* Polaroid Crime Scene Photo */}
        <div className="bg-white p-2 border border-stone-300 shadow-sm mb-2">
          <div className="w-full h-32 bg-stone-950 overflow-hidden relative flex items-center justify-center border border-stone-400">
            <img
              src={photoUrl}
              alt={evidence.item_name}
              className="w-full h-full object-cover grayscale contrast-125 opacity-90 group-hover:scale-105 transition duration-500"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <div className="absolute inset-0 bg-stone-900/10 pointer-events-none"></div>
          </div>
          <div className="mt-1 text-[10px] font-typewriter font-bold text-stone-700 text-center tracking-tight">
            EVIDENCE ID: #EV-0{evidence.id || index + 1} - {evidence.location_found || 'Hiện trường'}
          </div>
        </div>

        {/* Evidence Description */}
        <div className="space-y-1">
          <h4 className="text-sm font-bold font-serif text-stone-900 group-hover:text-amber-900 transition">
            {evidence.item_name}
          </h4>
          <p className="text-[11px] text-stone-700 font-mono leading-tight line-clamp-2">
            {evidence.description}
          </p>
        </div>
      </div>

      <div className="mt-2 pt-1 border-t border-stone-300 text-[10px] font-sans text-stone-500 font-bold flex justify-end">
        Xem phân tích tang vật →
      </div>
    </motion.div>
  );
}
