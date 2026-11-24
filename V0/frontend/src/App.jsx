import React, { useState } from 'react';
import { 
  Flame, 
  Sparkles, 
  BookOpen, 
  RefreshCw, 
  FolderOpen, 
  ShieldAlert 
} from 'lucide-react';

import CorkBoard from './components/CorkBoard';
import DocumentModal from './components/DocumentModal';
import SuspectSingleModal from './components/SuspectSingleModal';
import EvidenceSingleModal from './components/EvidenceSingleModal';
import ImageLightboxModal from './components/ImageLightboxModal';
import DetectiveNotebook from './components/DetectiveNotebook';
import GuessModal from './components/GuessModal';
import './App.css';

const INITIAL_CASE = {
  id: 1,
  title: "Bí Ẩn Vụ Án Mạng Tại Biệt Thự Cổ Blackwood",
  summary: "Vào đêm mưa bão ngày 15/10, ngài Arthur Blackwood - nhà sưu tầm cổ vật giàu có - được phát hiện tử vong tại phòng làm việc khóa kín trên tầng 2 của biệt thự.",
  difficulty: "Medium",
  status: "ready",
  victim: {
    name: "Arthur Blackwood",
    age: 62,
    occupation: "Nhà sưu tầm cổ vật & Doanh nhân",
    body_condition: "Tử thi hạ nhiệt độ còn 31.2°C (nhiệt độ môi trường 22°C), hoen tử thi cố định rõ ở vùng lưng và đùi. Vết thương thấu ngực do vật nhọn.",
    location_found: "Phòng làm việc tầng 2, Biệt thự Blackwood"
  },
  suspects: [
    {
      id: 1,
      name: "Quản gia William",
      age: 55,
      occupation: "Quản gia biệt thự",
      motive: "Tranh chấp tiền lương và sắp bị sa thải do làm hỏng đồ cổ quý.",
      alibi: "Lúc 21:00 - 22:00 đang chuẩn bị trà dưới bếp tầng 1 và không lên tầng 2.",
      persona: "Trầm lặng, lịch thiệp nhưng ẩn chứa sự bất mãn kéo dài.",
      is_culprit: false
    },
    {
      id: 2,
      name: "Julian Blackwood",
      age: 28,
      occupation: "Nhiếp ảnh gia tự do",
      motive: "Nợ nần cờ bạc chồng chất, ngài Arthur vừa từ chối gạch tên Julian khỏi di chúc.",
      alibi: "Khai rằng từ 21:15 đến 21:45 đang ở phòng đọc sách tầng 1 nói chuyện điện thoại.",
      persona: "Cháu trai nạn nhân, nông nổi, hoang phí, thường xuyên cãi lộn với nạn nhân.",
      is_culprit: true
    },
    {
      id: 3,
      name: "Bác sĩ Eleanor Vance",
      age: 42,
      occupation: "Bác sĩ gia đình",
      motive: "Nạn nhân phát hiện bác sĩ kê đơn thuốc giả để trục lợi bảo hiểm.",
      alibi: "Thăm khám cho nạn nhân lúc 20:30 và rời biệt thự lúc 21:00.",
      persona: "Thông minh, quyết đoán, giữ thái độ hợp tác với cảnh sát.",
      is_culprit: false
    }
  ],
  timeline: [
    { id: 1, event_time: "20:30 - 21:00", description: "Bác sĩ Eleanor thăm khám sức khỏe cho ngài Arthur tại phòng làm việc tầng 2.", location: "Phòng làm việc" },
    { id: 2, event_time: "21:00 - 21:15", description: "Quản gia William mang trà lên phòng ngài Arthur, sau đó trở xuống bếp.", location: "Tầng 1 & Tầng 2" },
    { id: 3, event_time: "21:20 - 21:35", description: "Julian lén lên tầng 2 cãi nhau với nạn nhân về di chúc và sát hại nạn nhân.", location: "Phòng làm việc" },
    { id: 4, event_time: "22:00", description: "Quản gia gõ cửa nhưng phòng khóa trong, phát hiện thi thể qua khe cửa.", location: "Phòng làm việc" }
  ],
  evidences: [
    { id: 1, item_name: "Mảnh thủy tinh vỡ dính máu", description: "Mảnh kính của chiếc đồng hồ đeo tay bị vỡ tìm thấy dưới gầm bàn.", location_found: "Dưới bàn làm việc", is_key_evidence: true },
    { id: 2, item_name: "Tách trà cúc La Mã", description: "Tách trà uống dở trên bàn, không phát hiện độc chất.", location_found: "Mặt bàn làm việc", is_key_evidence: false },
    { id: 3, item_name: "Sợi chỉ đỏ giắt cửa sổ", description: "Cửa sổ hướng ra ban công đóng không chặt, giắt một sợi chỉ từ áo len đỏ.", location_found: "Khe cửa sổ tầng 2", is_key_evidence: true }
  ],
  culprit_name: "Julian Blackwood",
  forensic_report: "Báo cáo khám nghiệm hiện trường & tử thi:\n- Tử thi nạn nhân Arthur Blackwood (62 tuổi) nằm sấp tại phòng làm việc.\n- Nhiệt độ tử thi đo được lúc 22:30 là 31.2°C. Nhiệt độ môi trường phòng làm việc 22°C.\n- Hoen tử thi xuất hiện ở vùng lưng và mông, đã cố định hoàn toàn.\n- Cứng tử thi lan rộng ở vùng cơ hàm, cổ và các khớp nhỏ tay chân.\n- Nguyên nhân tử vong trực tiếp: Mất máu cấp do vết thương xuyên thấu thất trái ngực bởi vật sắc nhọn."
};

export default function App() {
  const [caseData, setCaseData] = useState(INITIAL_CASE);
  const [isGenerating, setIsGenerating] = useState(false);

  // STATE MACHINE FOR INDEPENDENT MODALS
  // null
  // | { type: 'SUSPECT_DETAIL', suspect, index }
  // | { type: 'EVIDENCE_DETAIL', evidence, index }
  // | { type: 'FULL_DOSSIER', defaultTab: 'report' | 'suspects' | 'evidences' | 'timeline' }
  // | { type: 'IMAGE_LIGHTBOX', imageSrc, imageTitle }
  const [activeModal, setActiveModal] = useState(null);

  const [isNotebookOpen, setIsNotebookOpen] = useState(false);
  const [guessSuspect, setGuessSuspect] = useState(null);
  const [themeInput, setThemeInput] = useState("Vụ án mạng tại biệt thự cổ");
  const [difficulty, setDifficulty] = useState("Medium");

  const handleGenerateCase = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/cases/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: themeInput, difficulty })
      });

      if (!response.ok) {
        throw new Error("Không thể kết nối Backend");
      }

      const data = await response.json();
      pollCaseStatus(data.case_id);
    } catch (error) {
      console.warn("Backend API offline. Using Seed Case Mock Generator fallback:", error);
      setTimeout(() => {
        setCaseData(INITIAL_CASE);
        setIsGenerating(false);
      }, 1500);
    }
  };

  const pollCaseStatus = (caseId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/cases/${caseId}`);
        if (!res.ok) return;

        const data = await res.json();
        if (data.status === 'ready') {
          clearInterval(interval);
          setCaseData(data);
          setIsGenerating(false);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setIsGenerating(false);
          alert("Quá trình sinh vụ án gặp lỗi.");
        }
      } catch (e) {
        clearInterval(interval);
        setIsGenerating(false);
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col font-sans relative">
      <div className="vignette-overlay"></div>

      {/* HEADER TOP BAR */}
      <header className="relative z-40 bg-stone-900 border-b border-amber-900/40 px-6 py-3 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-amber-900/60 border border-amber-600 flex items-center justify-center text-amber-400 shadow">
            <Flame size={24} className="animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-noir tracking-wider text-amber-100 flex items-center gap-2">
              AI DETECTIVE AGENCY <span className="text-xs font-mono px-2 py-0.5 bg-amber-900/80 text-amber-300 rounded">9ROUTER GATEWAY</span>
            </h1>
            <p className="text-xs font-mono text-stone-400">
              Chuyên Án #POL-{caseData.id || '802'} | Trò chơi trinh thám tự động sinh bằng LLM
            </p>
          </div>
        </div>

        {/* Generator Controls */}
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={themeInput}
            onChange={(e) => setThemeInput(e.target.value)}
            placeholder="Nhập bối cảnh vụ án..."
            className="bg-stone-950 border border-stone-700 rounded px-3 py-1.5 text-xs text-stone-200 outline-none focus:border-amber-600 w-48 sm:w-64 font-mono"
          />

          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="bg-stone-950 border border-stone-700 rounded px-2.5 py-1.5 text-xs text-amber-300 font-mono outline-none"
          >
            <option value="Easy">Dễ (Easy)</option>
            <option value="Medium">Vừa (Medium)</option>
            <option value="Hard">Khó (Hard)</option>
          </select>

          <button
            onClick={handleGenerateCase}
            disabled={isGenerating}
            className="px-4 py-1.5 bg-amber-700 hover:bg-amber-600 disabled:opacity-50 text-white rounded font-mono text-xs font-bold transition shadow flex items-center gap-1.5"
          >
            {isGenerating ? (
              <>
                <RefreshCw size={14} className="animate-spin" /> Đang tạo qua 9Router...
              </>
            ) : (
              <>
                <Sparkles size={14} /> Sinh Vụ Án Mới
              </>
            )}
          </button>
        </div>
      </header>

      {/* TOOLBAR CONTROLS */}
      <div className="relative z-40 bg-stone-900/90 border-b border-stone-800 px-6 py-2 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveModal({ type: 'FULL_DOSSIER', defaultTab: 'report' })}
            className="flex items-center gap-1.5 px-3 py-1 bg-stone-800 hover:bg-stone-700 text-amber-200 rounded border border-stone-700 transition"
          >
            <FolderOpen size={14} /> Toàn Bộ Hồ Sơ Chuyên Án
          </button>

          <button
            onClick={() => setIsNotebookOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1 bg-stone-800 hover:bg-stone-700 text-amber-200 rounded border border-stone-700 transition"
          >
            <BookOpen size={14} /> Sổ Tay Thám Tử
          </button>
        </div>

        <div>
          <button
            onClick={() => setGuessSuspect(caseData?.suspects?.[0] || { id: 1 })}
            className="flex items-center gap-1.5 px-4 py-1 bg-red-800 hover:bg-red-700 text-white font-bold rounded shadow transition"
          >
            <ShieldAlert size={15} /> BẮT GIỮ HUNG THỦ
          </button>
        </div>
      </div>

      {/* MAIN CORKBOARD INTERACTIVE BOARD */}
      <main className="flex-1 p-4 md:p-6 relative z-10">
        <CorkBoard
          caseData={caseData}
          onOpenSuspect={(suspect, index) => setActiveModal({ type: 'SUSPECT_DETAIL', suspect, index })}
          onOpenEvidence={(evidence, index) => setActiveModal({ type: 'EVIDENCE_DETAIL', evidence, index })}
          onOpenReport={() => setActiveModal({ type: 'FULL_DOSSIER', defaultTab: 'report' })}
          onZoomImage={(imageSrc, imageTitle) => setActiveModal({ type: 'IMAGE_LIGHTBOX', imageSrc, imageTitle })}
        />
      </main>

      {/* STATE MACHINE INDEPENDENT MODALS */}

      {/* 1. Dedicated Single Suspect Interrogation Modal */}
      {activeModal?.type === 'SUSPECT_DETAIL' && (
        <SuspectSingleModal
          suspect={activeModal.suspect}
          index={activeModal.index}
          onClose={() => setActiveModal(null)}
          onSelectCulprit={(suspect) => {
            setActiveModal(null);
            setGuessSuspect(suspect);
          }}
        />
      )}

      {/* 2. Dedicated Single Evidence Analysis Modal */}
      {activeModal?.type === 'EVIDENCE_DETAIL' && (
        <EvidenceSingleModal
          evidence={activeModal.evidence}
          index={activeModal.index}
          onClose={() => setActiveModal(null)}
          onZoomImage={(imageSrc, imageTitle) => setActiveModal({ type: 'IMAGE_LIGHTBOX', imageSrc, imageTitle })}
        />
      )}

      {/* 3. Full Kraft Paper Dossier File */}
      {activeModal?.type === 'FULL_DOSSIER' && (
        <DocumentModal
          activeDoc={{ type: activeModal.defaultTab, caseData }}
          onClose={() => setActiveModal(null)}
          onSelectCulprit={(suspect) => {
            setActiveModal(null);
            setGuessSuspect(suspect);
          }}
        />
      )}

      {/* 4. Photo Zoom Lightbox Modal */}
      {activeModal?.type === 'IMAGE_LIGHTBOX' && (
        <ImageLightboxModal
          imageSrc={activeModal.imageSrc}
          imageTitle={activeModal.imageTitle}
          onClose={() => setActiveModal(null)}
        />
      )}

      {/* Floating Detective Notebook Drawer */}
      <DetectiveNotebook
        isOpen={isNotebookOpen}
        onClose={() => setIsNotebookOpen(false)}
      />

      {/* Accuse Culprit Modal */}
      {guessSuspect && (
        <GuessModal
          caseData={caseData}
          initialSuspect={guessSuspect}
          onClose={() => setGuessSuspect(null)}
        />
      )}
    </div>
  );
}
