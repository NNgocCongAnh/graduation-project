import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldAlert, X, CheckCircle2, XCircle, Award } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function GuessModal({ caseData, initialSuspect, onClose, onGuessSubmit }) {
  const [selectedSuspectId, setSelectedSuspectId] = useState(initialSuspect?.id || caseData?.suspects?.[0]?.id || null);
  const [reasoning, setReasoning] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null); // { is_correct: bool, message: str, actual_culprit_name: str }

  const suspects = caseData?.suspects || [];

  const handleSubmit = async () => {
    if (!selectedSuspectId) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/cases/${caseData.id}/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          suspect_id: selectedSuspectId,
          reasoning: reasoning
        })
      });

      if (!res.ok) {
        // Mock fallback check if backend not running
        const selSuspect = suspects.find(s => s.id === selectedSuspectId);
        const isCorrect = selSuspect?.name === caseData?.culprit_name;
        setResult({
          is_correct: isCorrect,
          message: isCorrect 
            ? `CHÍNH XÁC! Bạn đã phá án thành công. ${selSuspect?.name} chính là hung thủ thực sự.` 
            : `RẤT TIẾC! Lời buộc tội của bạn đã sai. ${selSuspect?.name} không phải hung thủ.`,
          actual_culprit_name: caseData?.culprit_name || 'Không xác định'
        });
        if (isCorrect) confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } });
        return;
      }

      const data = await res.json();
      setResult(data);
      if (data.is_correct) {
        confetti({ particleCount: 200, spread: 90, origin: { y: 0.6 } });
      }
    } catch (e) {
      console.error(e);
      // Offline fallback
      const selSuspect = suspects.find(s => s.id === selectedSuspectId);
      const isCorrect = selSuspect?.name === caseData?.culprit_name;
      setResult({
        is_correct: isCorrect,
        message: isCorrect 
          ? `CHÍNH XÁC! Bạn đã phá án thành công. ${selSuspect?.name} chính là hung thủ thực sự.` 
          : `RẤT TIẾC! Lời buộc tội của bạn đã sai. ${selSuspect?.name} không phải hung thủ.`,
        actual_culprit_name: caseData?.culprit_name || 'Julian Blackwood'
      });
      if (isCorrect) confetti({ particleCount: 200, spread: 90, origin: { y: 0.6 } });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-950/85 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="relative w-full max-w-lg bg-stone-900 border-2 border-red-700/80 text-stone-100 rounded-sm shadow-2xl overflow-hidden font-mono"
        >
          {/* Header */}
          <div className="bg-red-950 p-4 border-b border-red-800 flex items-center justify-between font-sans">
            <div className="flex items-center gap-2 text-red-100">
              <ShieldAlert className="text-red-500 animate-pulse" size={22} />
              <h3 className="font-bold text-base uppercase tracking-wider">CHỈ DANH HUNG THỦ VỤ ÁN</h3>
            </div>
            <button onClick={onClose} className="text-stone-400 hover:text-white p-1 rounded">
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-5">
            {!result ? (
              <>
                <p className="text-xs text-stone-300 font-sans leading-relaxed">
                  Xem xét kỹ lưỡng các mâu thuẫn trong lời khai, động cơ và báo cáo pháp y trước khi ra quyết định quy kết trách nhiệm hình sự.
                </p>

                {/* Suspect Radio Selector */}
                <div className="space-y-2">
                  <label className="text-xs font-sans uppercase font-bold text-amber-400">
                    Chọn nghi phạm chính:
                  </label>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {suspects.map((s) => (
                      <div
                        key={s.id}
                        onClick={() => setSelectedSuspectId(s.id)}
                        className={`p-3 rounded border cursor-pointer transition flex items-center justify-between ${
                          selectedSuspectId === s.id
                            ? 'bg-red-900/40 border-red-500 text-white font-bold'
                            : 'bg-stone-800 border-stone-700 text-stone-300 hover:bg-stone-750'
                        }`}
                      >
                        <div>
                          <div className="text-sm font-bold">{s.name}</div>
                          <div className="text-xs font-sans text-stone-400">{s.occupation} | {s.age} tuổi</div>
                        </div>
                        <input
                          type="radio"
                          name="suspect"
                          checked={selectedSuspectId === s.id}
                          onChange={() => setSelectedSuspectId(s.id)}
                          className="accent-red-600 w-4 h-4"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Reasoning text */}
                <div className="space-y-1">
                  <label className="text-xs font-sans uppercase font-bold text-amber-400">
                    Lý do suy luận của bạn (Không bắt buộc):
                  </label>
                  <textarea
                    value={reasoning}
                    onChange={(e) => setReasoning(e.target.value)}
                    placeholder="Giải thích mâu thuẫn thời gian chết hoặc chứng cứ ngoại phạm..."
                    rows={3}
                    className="w-full bg-stone-950 border border-stone-700 rounded p-2.5 text-xs text-stone-200 outline-none focus:border-red-500"
                  />
                </div>

                {/* Submit button */}
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting || !selectedSuspectId}
                  className="w-full py-3 bg-red-700 hover:bg-red-800 disabled:opacity-50 text-white font-sans font-bold uppercase tracking-wider rounded transition flex items-center justify-center gap-2 shadow-lg"
                >
                  {isSubmitting ? 'Đang kiểm tra lời buộc tội...' : 'Bắt giữ hung thủ này'}
                </button>
              </>
            ) : (
              /* Result view */
              <div className="text-center py-4 space-y-4">
                {result.is_correct ? (
                  <div className="space-y-3">
                    <div className="w-16 h-16 bg-emerald-950 border-2 border-emerald-500 rounded-full flex items-center justify-center mx-auto text-emerald-400">
                      <Award size={36} />
                    </div>
                    <h4 className="text-2xl font-bold text-emerald-400 font-sans uppercase">PHÁ ÁN THÀNH CÔNG!</h4>
                    <p className="text-stone-200 text-sm leading-relaxed">{result.message}</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="w-16 h-16 bg-red-950 border-2 border-red-500 rounded-full flex items-center justify-center mx-auto text-red-400">
                      <XCircle size={36} />
                    </div>
                    <h4 className="text-2xl font-bold text-red-500 font-sans uppercase">SUY LUẬN THẤT BẠI!</h4>
                    <p className="text-stone-200 text-sm leading-relaxed">{result.message}</p>
                    <div className="p-3 bg-stone-950 rounded border border-stone-800 text-xs text-amber-300">
                      Hung thủ thực sự: <strong>{result.actual_culprit_name}</strong>
                    </div>
                  </div>
                )}

                <button
                  onClick={onClose}
                  className="mt-4 px-6 py-2 bg-stone-700 hover:bg-stone-600 text-white font-sans text-xs font-bold rounded uppercase tracking-wider transition"
                >
                  Đóng cửa sổ
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
