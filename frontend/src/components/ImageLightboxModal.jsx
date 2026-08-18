import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ZoomIn, Camera } from 'lucide-react';

export default function ImageLightboxModal({ imageSrc, imageTitle, onClose }) {
  if (!imageSrc) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-950/90 backdrop-blur-md select-none font-mono">
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="relative max-w-3xl w-full bg-[#f4ebd0] p-4 sm:p-6 rounded-xs shadow-2xl border-4 border-stone-800 text-stone-900"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute -top-4 -right-4 w-9 h-9 rounded-full bg-stone-900 text-amber-100 hover:bg-red-800 flex items-center justify-center shadow-xl border border-stone-700 transition z-50"
          >
            <X size={20} />
          </button>

          {/* Polaroid Frame */}
          <div className="bg-white p-3 border-2 border-stone-400 shadow-md">
            <div className="relative w-full h-[65vh] bg-stone-950 overflow-hidden flex items-center justify-center border border-stone-500">
              <img
                src={imageSrc}
                alt={imageTitle}
                className="max-w-full max-h-full object-contain filter contrast-125 grayscale"
              />
              <div className="absolute inset-0 bg-stone-900/10 pointer-events-none"></div>
            </div>

            <div className="mt-3 flex items-center justify-between font-typewriter text-xs text-stone-800 border-t border-stone-300 pt-2">
              <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider">
                <Camera size={16} className="text-amber-900" />
                <span>ẢNH HIỆN TRƯỜNG: {imageTitle || 'VẬT CHỨNG'}</span>
              </div>
              <span className="text-stone-500">MÃ SỐ: POL-EVID-FULLRES</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
