import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldAlert, User, AlertCircle, Clock, FileText } from 'lucide-react';

export default function SuspectSingleModal({ suspect, index, onClose, onSelectCulprit }) {
  if (!suspect) return null;

  const mugshotUrl = (suspect.name.toLowerCase().includes('bác sĩ') || suspect.name.toLowerCase().includes('eleanor') || suspect.name.toLowerCase().includes('chị') || suspect.name.toLowerCase().includes('bà'))
    ? '/assets/mugshot_female.png'
    : '/assets/mugshot_male.png';

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

          {/* Header Badge */}
          <div className="border-b-2 border-stone-800 pb-3 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-[10px] font-sans font-bold uppercase tracking-widest bg-stone-900 text-amber-300 px-2 py-0.5 rounded">
                HỒ SƠ KHẨU CUNG CẢNH SÁT #{index !== undefined ? index + 1 : '01'}
              </span>
              <h2 className="text-2xl font-bold font-mono text-stone-900 mt-1">{suspect.name}</h2>
            </div>
            <div className="text-xs font-mono text-stone-700">
              {suspect.age} TUỔI | {suspect.occupation || 'Chưa rõ'}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-6">
            {/* Left Photo Mugshot */}
            <div className="sm:col-span-5 bg-white p-2 border-2 border-stone-400 shadow-md flex flex-col items-center">
              <div className="w-full h-44 bg-stone-950 overflow-hidden relative border border-stone-400">
                <img
                  src={mugshotUrl}
                  alt={suspect.name}
                  className="w-full h-full object-cover grayscale contrast-125"
                />
              </div>
              <div className="mt-2 text-center text-xs font-typewriter font-bold text-stone-800 tracking-wider">
                ID #SUSP-{suspect.id || '101'}
              </div>
            </div>

            {/* Right Details */}
            <div className="sm:col-span-7 space-y-4 font-mono text-xs">
              <div className="bg-amber-100/90 p-3 rounded border border-amber-300 shadow-xs">
                <strong className="text-amber-900 font-sans block text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                  <AlertCircle size={14} className="text-amber-700" /> Động cơ nghi vấn (Motive):
                </strong>
                <p className="text-stone-900 leading-relaxed">{suspect.motive || 'Chưa xác định động cơ cụ thể.'}</p>
              </div>

              <div className="bg-sky-100/90 p-3 rounded border border-sky-300 shadow-xs">
                <strong className="text-sky-900 font-sans block text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Clock size={14} className="text-sky-700" /> Lời khai Alibi (Chứng cứ ngoại phạm):
                </strong>
                <p className="text-stone-900 leading-relaxed font-mono font-bold">"{suspect.alibi || 'Không có chứng cứ ngoại phạm.'}"</p>
              </div>

              <div className="bg-stone-200/80 p-3 rounded border border-stone-300 text-[11px] font-sans text-stone-800">
                <strong>Tiểu sử & Tính cách:</strong> {suspect.persona || 'Không có ghi chú thêm.'}
              </div>
            </div>
          </div>

          {/* Action button */}
          <div className="mt-6 pt-4 border-t border-stone-400 flex items-center justify-between font-sans">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-stone-300 hover:bg-stone-400 text-stone-900 rounded text-xs font-bold transition"
            >
              Quay lại Bảng ghim
            </button>
            <button
              onClick={() => {
                onClose();
                onSelectCulprit(suspect);
              }}
              className="px-5 py-2 bg-red-800 hover:bg-red-900 text-white rounded text-xs font-bold uppercase tracking-wider transition flex items-center gap-1.5 shadow"
            >
              <ShieldAlert size={16} /> Bắt giữ hung thủ này
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
