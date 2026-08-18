import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  FileText, 
  User, 
  Clock, 
  Search, 
  ShieldAlert, 
  Activity, 
  Camera,
  FileSearch,
  CheckCircle2,
  Paperclip,
  Bookmark
} from 'lucide-react';

export default function DocumentModal({ activeDoc, onClose, onSelectCulprit }) {
  const [activeTab, setActiveTab] = useState(activeDoc?.type || 'report'); // 'report' | 'suspects' | 'evidences' | 'timeline'

  if (!activeDoc) return null;

  const { caseData } = activeDoc;
  const victim = caseData?.victim;
  const suspects = caseData?.suspects || [];
  const evidences = caseData?.evidences || [];
  const timeline = caseData?.timeline || [];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-stone-950/85 backdrop-blur-md overflow-y-auto">
        
        {/* PHYSICAL KRAFT PAPER FOLDER WRAPPER WITH DEPTH SHADOWS */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-5xl bg-[#c5a070] text-stone-900 rounded-sm shadow-2xl border-4 border-[#8c6b43] overflow-hidden my-6 font-mono"
          style={{
            backgroundImage: `radial-gradient(#ab895b 1px, transparent 1px), url('https://www.transparenttextures.com/patterns/cardboard.png')`,
            backgroundSize: '20px 20px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.85), inset 0 0 80px rgba(74, 52, 28, 0.5)'
          }}
        >
          {/* Metallic Paperclip Header Accent */}
          <div className="absolute top-2 left-10 z-40">
            <Paperclip size={36} className="text-stone-700 transform -rotate-12 drop-shadow-lg" />
          </div>

          {/* Folder String Tie Button Accent */}
          <div className="absolute top-4 right-16 z-40 hidden sm:flex flex-col items-center">
            <div className="w-8 h-8 rounded-full bg-amber-900 border-2 border-amber-950 shadow-inner flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-amber-600"></div>
            </div>
            <span className="text-[9px] font-sans font-bold text-amber-950 uppercase tracking-widest mt-0.5">FILE TIE</span>
          </div>

          {/* Top Vintage Folder Tab Bar */}
          <div className="bg-[#4a341c] text-amber-100 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between border-b-4 border-amber-950 font-sans shadow-md gap-3">
            <div className="flex items-center gap-3 pl-8">
              <ShieldAlert className="text-amber-400 animate-pulse shrink-0" size={24} />
              <div>
                <div className="text-[10px] tracking-widest text-amber-400 font-bold uppercase">
                  HỒ SƠ CHUYÊN ÁN #POL-{caseData?.id || '802'}
                </div>
                <h2 className="text-lg font-bold font-serif text-amber-100">
                  {caseData?.title || 'Bí Ẩn Vụ Án Mạng'}
                </h2>
              </div>
            </div>

            {/* Folder Index Tabs (Tabs dạng kẹp trang đánh dấu) */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 text-xs">
              <button
                onClick={() => setActiveTab('report')}
                className={`px-3.5 py-1.5 rounded-t-sm font-mono font-bold transition flex items-center gap-1.5 border-t-2 border-x ${
                  activeTab === 'report' 
                    ? 'bg-[#f4ecd8] text-amber-950 border-amber-800 shadow-md font-bold -translate-y-0.5' 
                    : 'bg-[#8c6b43]/70 text-amber-100 hover:bg-[#a37f54] border-amber-950'
                }`}
              >
                <Activity size={14} /> Pháp Y & Tử Thi
              </button>
              <button
                onClick={() => setActiveTab('suspects')}
                className={`px-3.5 py-1.5 rounded-t-sm font-mono font-bold transition flex items-center gap-1.5 border-t-2 border-x ${
                  activeTab === 'suspects' 
                    ? 'bg-[#f4ecd8] text-amber-950 border-amber-800 shadow-md font-bold -translate-y-0.5' 
                    : 'bg-[#8c6b43]/70 text-amber-100 hover:bg-[#a37f54] border-amber-950'
                }`}
              >
                <User size={14} /> Lời Khai Nghi Phạm ({suspects.length})
              </button>
              <button
                onClick={() => setActiveTab('evidences')}
                className={`px-3.5 py-1.5 rounded-t-sm font-mono font-bold transition flex items-center gap-1.5 border-t-2 border-x ${
                  activeTab === 'evidences' 
                    ? 'bg-[#f4ecd8] text-amber-950 border-amber-800 shadow-md font-bold -translate-y-0.5' 
                    : 'bg-[#8c6b43]/70 text-amber-100 hover:bg-[#a37f54] border-amber-950'
                }`}
              >
                <Camera size={14} /> Túi Tang Vật ({evidences.length})
              </button>
              <button
                onClick={() => setActiveTab('timeline')}
                className={`px-3.5 py-1.5 rounded-t-sm font-mono font-bold transition flex items-center gap-1.5 border-t-2 border-x ${
                  activeTab === 'timeline' 
                    ? 'bg-[#f4ecd8] text-amber-950 border-amber-800 shadow-md font-bold -translate-y-0.5' 
                    : 'bg-[#8c6b43]/70 text-amber-100 hover:bg-[#a37f54] border-amber-950'
                }`}
              >
                <Clock size={14} /> Dòng Thời Gian
              </button>
            </div>

            <button
              onClick={onClose}
              className="absolute top-3 right-3 p-1.5 rounded-full bg-stone-900/60 hover:bg-red-900 text-stone-300 hover:text-white transition"
            >
              <X size={20} />
            </button>
          </div>

          {/* INNER LAYERED PHYSICAL PAPER CONTAINER (Giấy Kraft / Giấy kẻ lề ố vàng) */}
          <div className="p-4 sm:p-8 max-h-[76vh] overflow-y-auto">
            <div className="bg-[#f4ecd8] text-stone-900 p-6 sm:p-8 rounded-xs shadow-2xl border border-amber-900/30 relative">
              
              {/* PAGE 1: BÁO CÁO PHÁP Y & SƠ ĐỒ TỔN THƯƠNG TỬ THI */}
              {activeTab === 'report' && (
                <div className="space-y-6">
                  {/* Official Police Incident Report Stamp Header */}
                  <div className="border-b-2 border-stone-800 pb-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="text-xs uppercase font-sans tracking-widest text-stone-600 font-bold">
                        CỤC CẢNH SÁT ĐIỀU TRA TỘI PHẠM HÌNH SỰ - CHUYÊN ÁN MẬT
                      </div>
                      <h3 className="text-2xl font-bold text-stone-900 font-mono tracking-tight mt-1 uppercase">
                        BIÊN BẢN KHÁM NGHIỆM TỬ THI & HIỆN TRƯỜNG
                      </h3>
                      <p className="text-xs font-mono text-stone-600 mt-1">
                        Mã định danh: POL-FORENSIC-802 | Bối cảnh: <strong className="text-amber-900">{caseData?.difficulty}</strong>
                      </p>
                    </div>

                    {/* RED CLASSIFIED RUBBER STAMP */}
                    <div className="rotate-[-10deg] border-4 border-red-700 text-red-700 px-5 py-2 text-center rounded font-mono font-black text-sm tracking-widest uppercase shadow-md shrink-0 bg-red-50/50">
                      TOP SECRET - CLASSIFIED
                    </div>
                  </div>

                  {/* Victim Details Box */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                    <div className="md:col-span-7 space-y-4">
                      <div className="bg-[#eadecc] p-4 rounded border border-stone-400 font-mono text-xs space-y-2">
                        <div className="flex justify-between border-b border-stone-300 pb-1">
                          <span className="text-stone-600 font-sans">Tên nạn nhân:</span>
                          <span className="font-bold text-stone-900 text-sm">{victim?.name || 'Arthur Blackwood'}</span>
                        </div>
                        <div className="flex justify-between border-b border-stone-300 pb-1">
                          <span className="text-stone-600 font-sans">Tuổi / Nghề nghiệp:</span>
                          <span className="font-semibold text-stone-800">{victim?.age || 62} tuổi | {victim?.occupation}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-stone-600 font-sans">Vị trí phát hiện:</span>
                          <span className="font-semibold text-amber-900">{victim?.location_found}</span>
                        </div>
                      </div>

                      {/* Forensic Text */}
                      <div className="bg-[#fffdf7] p-5 rounded border border-stone-400 shadow-inner font-mono text-xs leading-relaxed space-y-2">
                        <h4 className="text-xs font-sans font-bold uppercase tracking-wider text-amber-900 mb-2 flex items-center gap-1">
                          <FileSearch size={16} /> Ghi Chép Khám Nghiệm Sinh Học Tử Thi:
                        </h4>
                        <p className="text-stone-900 whitespace-pre-line">
                          {caseData?.forensic_report || victim?.body_condition}
                        </p>
                      </div>

                      <div className="p-3 bg-amber-100 border border-amber-400 rounded text-xs text-amber-900 font-sans">
                        <strong className="block font-bold uppercase tracking-wider mb-0.5">⚠️ Chú ý từ Bác sĩ Pháp y:</strong>
                        Báo cáo cố tình KHÔNG ghi trực tiếp thời gian tử vong. Hãy tính giờ chết bằng mức hạ nhiệt độ tử thi (trung bình giảm 0.8 - 1°C mỗi giờ).
                      </div>
                    </div>

                    {/* Right Anatomical Human Body Diagram Vector */}
                    <div className="md:col-span-5 bg-stone-950 text-stone-100 p-5 rounded border-2 border-stone-800 flex flex-col items-center justify-center relative shadow-inner">
                      <div className="text-[10px] font-mono uppercase tracking-widest text-amber-400 font-bold mb-3 text-center">
                        SƠ ĐỒ TỔN THƯƠNG TỬ THI (BODY DIAGRAM)
                      </div>

                      <div className="relative w-44 h-64 flex items-center justify-center">
                        <svg className="w-full h-full text-stone-600 stroke-current opacity-80" viewBox="0 0 100 200">
                          <circle cx="50" cy="25" r="15" strokeWidth="2" fill="none" />
                          <rect x="46" y="40" width="8" height="10" strokeWidth="2" fill="none" />
                          <path d="M 25 50 L 75 50 L 68 120 L 32 120 Z" strokeWidth="2" fill="none" />
                          <path d="M 25 50 L 10 110 M 75 50 L 90 110" strokeWidth="2" fill="none" />
                          <path d="M 38 120 L 32 190 M 62 120 L 68 190" strokeWidth="2" fill="none" />
                        </svg>

                        {/* Chest Wound Marker */}
                        <motion.div 
                          initial={{ scale: 0 }} 
                          animate={{ scale: [1, 1.2, 1] }} 
                          transition={{ repeat: Infinity, duration: 2 }}
                          className="absolute top-16 left-[44%] w-4 h-4 rounded-full bg-red-600 border-2 border-white shadow-lg cursor-pointer group flex items-center justify-center"
                        >
                          <span className="w-1.5 h-1.5 bg-white rounded-full"></span>
                          <div className="hidden group-hover:block absolute bottom-6 left-1/2 -translate-x-1/2 w-48 bg-red-950 text-white text-[11px] p-2 rounded shadow-xl border border-red-500 font-sans z-50">
                            <strong>Vết thương thấu ngực:</strong> Do vật sắc nhọn đâm xuyên thất trái.
                          </div>
                        </motion.div>
                      </div>

                      <div className="mt-2 text-[10px] text-stone-400 font-sans text-center">
                        * Rê chuột vào điểm đỏ trên cơ thể để xem thương tổn.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* PAGE 2: LỜI KHAI NGHI PHẠM (INTERROGATION TRANSCRIPTS) */}
              {activeTab === 'suspects' && (
                <div className="space-y-6">
                  <div className="border-b-2 border-stone-800 pb-3 flex items-center justify-between">
                    <h3 className="text-xl font-bold text-stone-900 font-mono">BIÊN BẢN LỜI KHAI NGHI PHẠM</h3>
                    <span className="text-xs font-sans text-stone-600">Tổng cộng {suspects.length} nghi phạm</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {suspects.map((s, idx) => (
                      <div key={s.id || idx} className="bg-[#fffdf7] p-5 rounded border-2 border-stone-400 shadow-md space-y-3 font-mono text-xs relative">
                        <div className="flex items-center justify-between border-b border-stone-300 pb-1">
                          <span className="font-bold text-amber-900 uppercase">NGHI PHẠM #{idx + 1}</span>
                          <span className="text-stone-600">{s.age} tuổi | {s.occupation}</span>
                        </div>

                        <h4 className="text-lg font-bold font-serif text-stone-900">{s.name}</h4>

                        <div className="space-y-2">
                          <div className="bg-amber-100/70 p-2.5 rounded border border-amber-300">
                            <strong className="text-amber-900 font-sans block text-[10px] uppercase font-bold">🎯 Động cơ nghi vấn:</strong>
                            <p className="text-stone-900">{s.motive}</p>
                          </div>

                          <div className="bg-sky-100/70 p-2.5 rounded border border-sky-300">
                            <strong className="text-sky-900 font-sans block text-[10px] uppercase font-bold">🕒 Chứng cứ ngoại phạm (Alibi):</strong>
                            <p className="text-stone-900">{s.alibi}</p>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            onClose();
                            onSelectCulprit(s);
                          }}
                          className="mt-3 w-full py-2 bg-red-800 hover:bg-red-900 text-white font-sans font-bold text-xs uppercase rounded transition flex items-center justify-center gap-1.5 shadow"
                        >
                          <ShieldAlert size={14} /> Quy kết tội danh hung thủ
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PAGE 3: TÚI TANG VẬT HIỆN TRƯỜNG (EVIDENCE BAGS & PHOTOS) */}
              {activeTab === 'evidences' && (
                <div className="space-y-6">
                  <div className="border-b-2 border-stone-800 pb-3">
                    <h3 className="text-xl font-bold text-stone-900 font-mono">DANH MỤC TÚI TANG VẬT THU THẬP</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {evidences.map((e, idx) => (
                      <div key={e.id || idx} className="bg-[#fffdf7] p-4 rounded border-2 border-stone-400 shadow-md font-mono text-xs space-y-3">
                        <div className="flex items-center justify-between border-b border-stone-300 pb-1">
                          <span className="font-bold text-stone-900 text-sm">{e.item_name}</span>
                          {e.is_key_evidence && (
                            <span className="bg-red-700 text-white font-sans text-[9px] uppercase font-bold px-2 py-0.5 rounded">
                              ★ TANG VẬT MẤU CHỐT
                            </span>
                          )}
                        </div>

                        {/* Polaroid Evidence Photo Thumbnail */}
                        <div className="bg-white p-2 border border-stone-300 shadow-sm flex items-center gap-3">
                          <div className="w-24 h-24 bg-stone-900 overflow-hidden shrink-0 border border-stone-400">
                            <img
                              src={e.item_name.toLowerCase().includes('trà') ? '/assets/evidence_teacup.png' : '/assets/evidence_glass.png'}
                              alt={e.item_name}
                              className="w-full h-full object-cover grayscale contrast-125"
                            />
                          </div>
                          <div className="text-[11px] leading-relaxed text-stone-800">
                            <p><strong>Vị trí thu thập:</strong> {e.location_found || 'Hiện trường'}</p>
                            <p className="mt-1">{e.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PAGE 4: DÒNG THỜI GIAN TIMELINE */}
              {activeTab === 'timeline' && (
                <div className="space-y-6 font-mono">
                  <div className="border-b-2 border-stone-800 pb-3">
                    <h3 className="text-xl font-bold text-stone-900">TIMELINE DIỄN BIẾN VỤ ÁN</h3>
                  </div>

                  <div className="relative border-l-2 border-amber-900 ml-4 space-y-6 pl-6">
                    {timeline.map((t, idx) => (
                      <div key={t.id || idx} className="relative">
                        <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-amber-800 border-2 border-white"></div>
                        <div className="bg-[#fffdf7] p-4 rounded border border-stone-300 text-xs space-y-1">
                          <div className="font-bold text-amber-900 text-sm">{t.event_time}</div>
                          <div className="text-stone-800 leading-relaxed font-sans">{t.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* Folder Footer */}
          <div className="bg-[#382614] px-6 py-3 border-t-2 border-amber-950 flex items-center justify-between text-xs font-sans text-amber-200">
            <div>Hồ sơ điều tra chuyên án mật - Lưu trữ Cục Cảnh sát</div>
            <button
              onClick={onClose}
              className="px-5 py-1.5 bg-amber-800 hover:bg-amber-700 text-white rounded font-bold transition shadow"
            >
              Gấp hồ sơ
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
