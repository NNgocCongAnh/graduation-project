import React, { useState, useEffect } from 'react';
import { BookOpen, X, Save, CheckSquare, Square } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DetectiveNotebook({ isOpen, onClose }) {
  const [notes, setNotes] = useState(() => {
    return localStorage.getItem('detective_notebook') || '';
  });
  const [savedMessage, setSavedMessage] = useState(false);

  useEffect(() => {
    localStorage.setItem('detective_notebook', notes);
  }, [notes]);

  const handleSave = () => {
    localStorage.setItem('detective_notebook', notes);
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2000);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed top-0 right-0 h-full w-full sm:w-96 bg-[#2b2118] text-amber-100 shadow-2xl border-l-4 border-amber-900/60 z-50 flex flex-col font-serif"
          style={{
            backgroundImage: `linear-gradient(to right, rgba(0,0,0,0.4) 0%, transparent 10%), url('https://www.transparenttextures.com/patterns/leather.png')`
          }}
        >
          {/* Notebook Header */}
          <div className="bg-[#1c150f] p-4 border-b border-amber-900/40 flex items-center justify-between font-sans">
            <div className="flex items-center gap-2">
              <BookOpen className="text-amber-500" size={20} />
              <h3 className="font-bold text-amber-200 text-sm tracking-wider uppercase">SỔ TAY THÁM TỬ</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded text-amber-400 hover:text-white hover:bg-amber-950/50 transition"
            >
              <X size={20} />
            </button>
          </div>

          {/* Notebook Body (Paper lines background) */}
          <div className="flex-1 p-6 bg-[#f4ecd8] text-stone-900 overflow-y-auto flex flex-col font-mono shadow-inner relative">
            <div className="text-xs font-sans uppercase font-bold text-stone-600 border-b border-stone-400 pb-2 mb-3 flex items-center justify-between">
              <span>GHI CHÉP SUY LUẬN BẢN THÂN</span>
              {savedMessage && <span className="text-emerald-700 font-bold text-[10px] animate-pulse">✓ ĐÃ LƯU</span>}
            </div>

            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Nhập suy luận của bạn tại đây... (Ví dụ: Giờ chết ước tính lúc 21:30 dựa theo nhiệt độ tử thi 31.2°C...)"
              className="flex-1 bg-transparent border-none outline-none resize-none text-sm leading-relaxed text-stone-900 font-serif placeholder:text-stone-500/70"
            />
          </div>

          {/* Notebook Footer */}
          <div className="p-3 bg-[#1c150f] border-t border-amber-900/40 flex items-center justify-between text-xs font-sans">
            <span className="text-stone-400 text-[11px]">Tự động lưu vào trình duyệt</span>
            <button
              onClick={handleSave}
              className="px-3 py-1.5 bg-amber-700 hover:bg-amber-600 text-white rounded font-bold transition flex items-center gap-1.5"
            >
              <Save size={14} /> Lưu ngay
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
