import React, { useState } from 'react';
import { Trash2, Pin, Palette } from 'lucide-react';
import { motion } from 'framer-motion';

const COLOR_MAP = {
  yellow: {
    bg: 'bg-amber-100 dark:bg-amber-200 text-stone-900 border-amber-300',
    header: 'bg-amber-200/80',
    shadow: 'shadow-amber-950/40'
  },
  red: {
    bg: 'bg-rose-100 dark:bg-rose-200 text-stone-900 border-rose-300',
    header: 'bg-rose-200/80',
    shadow: 'shadow-rose-950/40'
  },
  green: {
    bg: 'bg-emerald-100 dark:bg-emerald-200 text-stone-900 border-emerald-300',
    header: 'bg-emerald-200/80',
    shadow: 'shadow-emerald-950/40'
  },
  blue: {
    bg: 'bg-sky-100 dark:bg-sky-200 text-stone-900 border-sky-300',
    header: 'bg-sky-200/80',
    shadow: 'shadow-sky-950/40'
  },
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-200 text-stone-900 border-purple-300',
    header: 'bg-purple-200/80',
    shadow: 'shadow-purple-950/40'
  }
};

export default function StickyNote({ note, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState(note.text || '');
  const [color, setColor] = useState(note.color || 'yellow');

  const currentColor = COLOR_MAP[color] || COLOR_MAP.yellow;

  const handleBlur = () => {
    setIsEditing(false);
    onUpdate({ ...note, text, color });
  };

  const handleColorChange = (newColor) => {
    setColor(newColor);
    onUpdate({ ...note, text, color: newColor });
  };

  return (
    <motion.div
      drag
      dragConstraints={{ left: -300, right: 600, top: -200, bottom: 400 }}
      dragElastic={0.1}
      whileHover={{ scale: 1.03, rotate: 0 }}
      whileTap={{ scale: 0.98 }}
      initial={{ scale: 0, rotate: note.rotation || -3 }}
      animate={{ scale: 1, rotate: note.rotation || -3 }}
      exit={{ scale: 0 }}
      className={`absolute w-56 p-4 rounded-sm border shadow-lg ${currentColor.bg} ${currentColor.shadow} cursor-grab active:cursor-grabbing font-mono transition-shadow z-20`}
      style={{ left: note.x || 100, top: note.y || 100 }}
    >
      {/* Ghim trên giấy nhớ */}
      <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-30">
        <div className="w-5 h-5 rounded-full bg-red-600 border-2 border-amber-100 shadow-md flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full bg-red-300"></div>
        </div>
      </div>

      {/* Header điều khiển */}
      <div className="flex items-center justify-between border-b border-stone-800/10 pb-1 mb-2 text-xs font-sans text-stone-600">
        <span className="font-semibold uppercase tracking-wider text-[10px]">📌 Ghi chú</span>
        <div className="flex items-center gap-1">
          {/* Menu đổi màu */}
          <div className="flex items-center gap-0.5 mr-1">
            {Object.keys(COLOR_MAP).map((cKey) => (
              <button
                key={cKey}
                onClick={() => handleColorChange(cKey)}
                className={`w-3.5 h-3.5 rounded-full border border-stone-400/50 ${
                  cKey === 'yellow' ? 'bg-amber-300' :
                  cKey === 'red' ? 'bg-rose-400' :
                  cKey === 'green' ? 'bg-emerald-400' :
                  cKey === 'blue' ? 'bg-sky-400' : 'bg-purple-400'
                } ${color === cKey ? 'ring-2 ring-stone-800 scale-110' : 'opacity-70 hover:opacity-100'}`}
                title={`Đổi màu ${cKey}`}
              />
            ))}
          </div>

          <button
            onClick={() => onDelete(note.id)}
            className="p-0.5 hover:bg-stone-800/10 rounded text-stone-700 hover:text-red-700 transition"
            title="Xóa giấy nhớ"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* Nội dung Giấy nhớ */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={handleBlur}
        placeholder="Gõ suy luận hoặc manh mối..."
        rows={4}
        className="w-full bg-transparent resize-none border-none outline-none text-sm leading-relaxed font-sans font-medium text-stone-900 placeholder:text-stone-500/70"
      />
    </motion.div>
  );
}
