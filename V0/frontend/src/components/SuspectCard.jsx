import React from 'react';
import { motion } from 'framer-motion';
import { Pin, Paperclip, User, AlertCircle } from 'lucide-react';

export default function SuspectCard({ suspect, index, isSelected, onPinClick, onOpenDetail }) {
  const cardId = `suspect-${suspect.id || index + 1}`;

  // Map avatar image: female or male mugshots
  const mugshotUrl = (suspect.name.toLowerCase().includes('bác sĩ') || suspect.name.toLowerCase().includes('eleanor') || suspect.name.toLowerCase().includes('chị') || suspect.name.toLowerCase().includes('bà'))
    ? '/assets/mugshot_female.png'
    : '/assets/mugshot_male.png';

  return (
    <motion.div
      initial={{ rotate: index % 2 === 0 ? 1.5 : -2, y: 10, opacity: 0 }}
      animate={{ rotate: index % 2 === 0 ? 1.5 : -2, y: 0, opacity: 1 }}
      whileHover={{ scale: 1.04, rotate: 0, zIndex: 30 }}
      className="relative w-64 bg-[#f2ebd9] text-stone-900 rounded-sm p-4 border border-amber-900/40 shadow-2xl font-mono flex flex-col justify-between cursor-pointer select-none group"
      style={{
        boxShadow: '10px 14px 28px rgba(0,0,0,0.65)',
        backgroundImage: `radial-gradient(#e0d5be 1px, transparent 1px)`,
        backgroundSize: '16px 16px'
      }}
      onClick={() => onOpenDetail(suspect)}
    >
      {/* Top Metallic Paperclip Accent */}
      <div className="absolute -top-3 left-6 z-30 opacity-90 pointer-events-none">
        <Paperclip size={28} className="text-stone-700 transform rotate-12 drop-shadow-md" />
      </div>

      {/* Red Thumbtack Pin Button for Red String Connections */}
      <button
        id={`pin-${cardId}`}
        onClick={(e) => {
          e.stopPropagation();
          onPinClick(e, { id: cardId, name: suspect.name });
        }}
        className={`absolute -top-3.5 right-6 w-7 h-7 rounded-full flex items-center justify-center transition shadow-xl z-40 ${
          isSelected 
            ? 'bg-amber-400 ring-4 ring-amber-300 scale-125' 
            : 'bg-red-600 hover:bg-red-500 hover:scale-110'
        }`}
        title={`Nối dây chỉ đỏ cho nghi phạm ${suspect.name}`}
      >
        <Pin size={14} className="text-white transform -rotate-45" />
      </button>

      <div>
        {/* Police Badge Stamp Header */}
        <div className="flex items-center justify-between border-b-2 border-stone-800/80 pb-1 mb-3">
          <span className="text-[10px] font-sans font-bold uppercase tracking-widest bg-stone-900 text-amber-300 px-2 py-0.5 rounded-xs">
            HỒ SƠ NGHI PHẠM #{index + 1}
          </span>
          <span className="text-xs font-bold text-stone-700">{suspect.age} TUỔI</span>
        </div>

        {/* Vintage Polaroid Mugshot Frame */}
        <div className="bg-white p-2.5 shadow-md border border-stone-300 rounded-xs mb-3 flex flex-col items-center">
          <div className="w-full h-36 bg-stone-950 overflow-hidden relative border border-stone-400 flex items-center justify-center">
            <img
              src={mugshotUrl}
              alt={suspect.name}
              className="w-full h-full object-cover grayscale contrast-125 opacity-90 group-hover:scale-105 transition duration-500"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            {/* Fallback Icon */}
            <User size={48} className="text-stone-600 absolute" />
            <div className="absolute inset-0 bg-amber-950/20 mix-blend-color-burn pointer-events-none"></div>
          </div>
          <div className="w-full text-center mt-1.5 font-typewriter text-[11px] font-bold text-stone-800 tracking-wider uppercase border-t border-stone-200 pt-1">
            ID #SUSP-{suspect.id || index + 101}
          </div>
        </div>

        {/* Suspect Name & Occupation */}
        <div className="space-y-1 mb-3">
          <h4 className="text-base font-bold font-serif text-stone-900 leading-tight group-hover:text-amber-900 transition">
            {suspect.name}
          </h4>
          <p className="text-[11px] text-stone-700 font-sans">
            <strong>Nghề nghiệp:</strong> {suspect.occupation || 'Chưa rõ'}
          </p>
        </div>

        {/* Alibi Snippet Taped Note */}
        <div className="relative bg-amber-100/90 border border-amber-300/80 p-2.5 rounded-xs text-[11px] leading-relaxed shadow-sm">
          {/* Tape styling on top left */}
          <div className="absolute -top-2 left-3 w-8 h-3 bg-amber-200/70 border-x border-stone-400/50 transform -rotate-6"></div>
          <strong className="block text-[10px] font-sans font-bold uppercase tracking-wider text-amber-900 mb-0.5 flex items-center gap-1">
            <AlertCircle size={12} className="text-amber-700" /> Trích lời khai Alibi:
          </strong>
          <p className="text-stone-900 font-mono italic line-clamp-2">
            "{suspect.alibi || 'Không có bằng chứng ngoại phạm.'}"
          </p>
        </div>
      </div>

      {/* Footer hint */}
      <div className="mt-3 pt-2 border-t border-stone-300/80 flex items-center justify-between text-[10px] font-sans text-amber-900 font-bold">
        <span>Bấm để lật hồ sơ</span>
        <span className="group-hover:translate-x-1 transition font-mono">→</span>
      </div>
    </motion.div>
  );
}
