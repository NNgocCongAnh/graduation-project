import React from 'react';

export default function RedStringOverlay({ redStrings, getCardCenter, onRemoveString }) {
  return (
    <svg className="pointer-events-none absolute inset-0 z-30 w-full h-full overflow-visible">
      <defs>
        {/* Đổ bóng 3D nổi cho sợi chỉ đỏ */}
        <filter id="string-shadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="3" dy="4" stdDeviation="2.5" floodColor="#000000" floodOpacity="0.7" />
        </filter>
      </defs>

      {redStrings.map((string) => {
        const start = getCardCenter(string.fromId);
        const end = getCardCenter(string.toId);

        if (!start || !end || (start.x === 0 && start.y === 0) || (end.x === 0 && end.y === 0)) return null;

        // Tính điểm uốn cong Quadratic Bezier Q ở giữa (Độ võng tự nhiên do trọng lực)
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2 + 35; // Võng xuống 35px

        return (
          <g key={string.id} className="pointer-events-auto cursor-pointer group" onClick={() => onRemoveString(string.id)}>
            {/* Vùng cảm ứng click rộng cho sợi chỉ */}
            <path
              d={`M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`}
              fill="none"
              stroke="transparent"
              strokeWidth="16"
            />
            {/* Sợi chỉ đỏ chính (Red 700) */}
            <path
              d={`M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`}
              fill="none"
              stroke="#b91c1c"
              strokeWidth="3.5"
              strokeLinecap="round"
              filter="url(#string-shadow)"
              className="group-hover:stroke-amber-400 transition duration-200"
            />
            {/* Vệt sáng đứt nét trên sợi chỉ */}
            <path
              d={`M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`}
              fill="none"
              stroke="#ef4444"
              strokeWidth="1.2"
              strokeDasharray="4,6"
              strokeLinecap="round"
            />
          </g>
        );
      })}
    </svg>
  );
}
