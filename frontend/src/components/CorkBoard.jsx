import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pin, Search, User, FileText, Plus, Paperclip } from 'lucide-react';
import StickyNote from './StickyNote';
import SuspectCard from './SuspectCard';
import EvidenceCard from './EvidenceCard';
import RedStringOverlay from './RedStringOverlay';

export default function CorkBoard({ caseData, onOpenSuspect, onOpenEvidence, onOpenReport, onZoomImage }) {
  const [stickyNotes, setStickyNotes] = useState([
    { id: 1, text: '💡 Kiểm tra mâu thuẫn thời gian giữa alibi nghi phạm & hoen tử thi!', color: 'yellow', x: 20, y: 360, rotation: -4 },
    { id: 2, text: '❓ Ai sở hữu mảnh kính đồng hồ vỡ dính máu?', color: 'red', x: 620, y: 390, rotation: 3 }
  ]);

  // Red String Connection System
  const [selectedPinNode, setSelectedPinNode] = useState(null);
  const [redStrings, setRedStrings] = useState([
    { id: 'str-1', fromId: 'victim-1', toId: 'suspect-2' }
  ]);

  const boardRef = useRef(null);

  const victim = caseData?.victim;
  const suspects = caseData?.suspects || [];
  const evidences = caseData?.evidences || [];

  const handlePinClick = (e, node) => {
    e.stopPropagation();
    if (!selectedPinNode) {
      setSelectedPinNode(node);
    } else if (selectedPinNode.id === node.id) {
      setSelectedPinNode(null);
    } else {
      const existing = redStrings.find(
        (s) => (s.fromId === selectedPinNode.id && s.toId === node.id) || (s.fromId === node.id && s.toId === selectedPinNode.id)
      );

      if (!existing) {
        setRedStrings([...redStrings, { id: `str-${Date.now()}`, fromId: selectedPinNode.id, toId: node.id }]);
      }
      setSelectedPinNode(null);
    }
  };

  const removeRedString = (stringId) => {
    setRedStrings(redStrings.filter((s) => s.id !== stringId));
  };

  const handleAddStickyNote = () => {
    const newNote = {
      id: Date.now(),
      text: 'Ghi chú suy luận...',
      color: ['yellow', 'red', 'green', 'blue', 'purple'][Math.floor(Math.random() * 5)],
      x: 200 + Math.random() * 200,
      y: 150 + Math.random() * 100,
      rotation: Math.floor(Math.random() * 10) - 5
    };
    setStickyNotes([...stickyNotes, newNote]);
  };

  const handleUpdateStickyNote = (updated) => {
    setStickyNotes(stickyNotes.map((n) => (n.id === updated.id ? updated : n)));
  };

  const handleDeleteStickyNote = (id) => {
    setStickyNotes(stickyNotes.filter((n) => n.id !== id));
  };

  const getCardCenter = (cardId) => {
    const el = document.getElementById(`pin-${cardId}`);
    if (!el || !boardRef.current) return { x: 0, y: 0 };
    const boardRect = boardRef.current.getBoundingClientRect();
    const pinRect = el.getBoundingClientRect();
    return {
      x: pinRect.left - boardRect.left + pinRect.width / 2,
      y: pinRect.top - boardRect.top + pinRect.height / 2
    };
  };

  return (
    <div
      ref={boardRef}
      className="relative w-full min-h-[85vh] p-6 sm:p-8 rounded-lg shadow-2xl border-8 border-[#2d1b10] overflow-hidden font-sans select-none"
      style={{
        backgroundColor: '#6b472e',
        backgroundImage: `
          radial-gradient(circle at 50% 50%, rgba(35, 20, 10, 0.45) 0%, rgba(15, 8, 4, 0.88) 100%),
          url('https://www.transparenttextures.com/patterns/cork-board.png')
        `,
        backgroundBlendMode: 'multiply'
      }}
    >
      {/* Organic Quadratic Bezier Red Strings Overlay */}
      <RedStringOverlay
        redStrings={redStrings}
        getCardCenter={getCardCenter}
        onRemoveString={removeRedString}
      />

      {/* Top Control Bar */}
      <div className="absolute top-4 left-6 z-40 flex items-center gap-3 bg-stone-950/90 text-amber-100 px-4 py-2 rounded-full border border-amber-900/60 shadow-2xl backdrop-blur-md text-xs font-mono">
        {selectedPinNode ? (
          <span className="text-amber-400 font-bold flex items-center gap-1.5 animate-pulse">
            📌 Đang chọn "{selectedPinNode.name}" → Click ghim thẻ tiếp theo để NỐI DÂY CHỈ ĐỎ!
          </span>
        ) : (
          <span className="text-stone-300">
            💡 Click biểu tượng <Pin size={13} className="inline text-red-500" /> trên thẻ bất kỳ để <strong>nối dây chỉ đỏ suy luận</strong>.
          </span>
        )}

        <button
          onClick={handleAddStickyNote}
          className="ml-2 px-3 py-1 bg-amber-700 hover:bg-amber-600 text-white font-sans font-bold rounded-full transition flex items-center gap-1 text-[11px]"
        >
          <Plus size={14} /> Dán Giấy Nhớ
        </button>
      </div>

      {/* MAIN CARDS LAYOUT */}
      <div className="relative z-20 grid grid-cols-1 md:grid-cols-12 gap-8 mt-12">
        
        {/* VICTIM CARD (NẠN NHÂN) */}
        <div className="md:col-span-4 flex justify-center">
          <motion.div
            initial={{ rotate: -2 }}
            whileHover={{ scale: 1.03, rotate: -1 }}
            className="w-full max-w-sm bg-[#f2ebd9] text-stone-900 p-5 rounded-sm border-2 border-stone-400 shadow-2xl relative font-serif"
            style={{
              boxShadow: '10px 14px 28px rgba(0,0,0,0.65)'
            }}
          >
            {/* Paperclip Accent */}
            <div className="absolute -top-3 left-6 z-30 opacity-90 pointer-events-none">
              <Paperclip size={28} className="text-stone-700 transform rotate-12 drop-shadow-md" />
            </div>

            {/* Red Pin Button */}
            <button
              id="pin-victim-1"
              onClick={(e) => handlePinClick(e, { id: 'victim-1', name: victim?.name || 'Nạn nhân' })}
              className={`absolute -top-3.5 right-6 w-7 h-7 rounded-full flex items-center justify-center transition shadow-xl z-40 ${
                selectedPinNode?.id === 'victim-1'
                  ? 'bg-amber-400 ring-4 ring-amber-300 scale-125'
                  : 'bg-red-600 hover:scale-110'
              }`}
              title="Nối dây chỉ đỏ cho Nạn nhân"
            >
              <Pin size={14} className="text-white transform -rotate-45" />
            </button>

            <div className="border-b-2 border-stone-800/80 pb-1 mb-3 flex items-center justify-between font-mono">
              <span className="text-[10px] font-sans font-bold uppercase tracking-widest bg-stone-900 text-amber-100 px-2 py-0.5 rounded-xs">
                HỒ SƠ NẠN NHÂN
              </span>
              <span className="text-xs font-bold text-stone-700">{victim?.age || 62} TUỔI</span>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-20 h-24 bg-stone-900 border border-stone-400 flex flex-col items-center justify-center text-stone-300 text-[10px] uppercase font-mono shadow-inner shrink-0 relative overflow-hidden">
                <User size={36} className="text-stone-500" />
                <span className="mt-1 font-bold text-[9px]">VICTIM</span>
              </div>

              <div className="space-y-1 text-xs font-mono">
                <h3 className="text-lg font-bold font-serif text-stone-900">{victim?.name || 'Arthur Blackwood'}</h3>
                <p className="text-stone-700"><strong>Nghề nghiệp:</strong> {victim?.occupation}</p>
                <p className="text-amber-900 font-semibold">📍 {victim?.location_found}</p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-stone-300 text-xs font-mono text-stone-800 line-clamp-3">
              <strong>Tử thi:</strong> {victim?.body_condition}
            </div>

            <button
              onClick={onOpenReport}
              className="mt-4 w-full py-2 bg-stone-900 hover:bg-stone-800 text-amber-100 font-sans text-xs font-bold rounded-xs transition flex items-center justify-center gap-1.5 shadow"
            >
              <FileText size={14} /> Mở Hồ Sơ Pháp Y Mật
            </button>
          </motion.div>
        </div>

        {/* SUSPECTS SECTION */}
        <div className="md:col-span-8 flex flex-wrap gap-6 justify-center md:justify-start">
          {suspects.map((suspect, idx) => (
            <SuspectCard
              key={suspect.id || idx}
              suspect={suspect}
              index={idx}
              isSelected={selectedPinNode?.id === `suspect-${suspect.id || idx + 1}`}
              onPinClick={handlePinClick}
              onOpenDetail={(s) => onOpenSuspect(s, idx)}
            />
          ))}
        </div>

        {/* EVIDENCE CARDS SECTION */}
        <div className="md:col-span-12 mt-4">
          <div className="bg-stone-950/85 text-amber-100 p-4 rounded border border-amber-900/50 backdrop-blur-md">
            <div className="text-xs uppercase tracking-widest font-mono text-amber-400 font-bold mb-3 flex items-center justify-between">
              <span>📌 ẢNH CHỤP VẬT CHỨNG HIỆN TRƯỜNG (EVIDENCE PHOTOS)</span>
            </div>

            <div className="flex flex-wrap gap-6 justify-center md:justify-start">
              {evidences.map((item, idx) => (
                <EvidenceCard
                  key={item.id || idx}
                  evidence={item}
                  index={idx}
                  isSelected={selectedPinNode?.id === `evidence-${item.id || idx + 1}`}
                  onPinClick={handlePinClick}
                  onOpenDetail={(e) => onOpenEvidence(e, idx)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* STICKY NOTES LAYER */}
      <AnimatePresence>
        {stickyNotes.map((note) => (
          <StickyNote
            key={note.id}
            note={note}
            onUpdate={handleUpdateStickyNote}
            onDelete={handleDeleteStickyNote}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
