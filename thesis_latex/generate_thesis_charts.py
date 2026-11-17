import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures", exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

# 1. Bar Chart: Pass Rate Comparison
models = ['gpt-4o-mini', 'gpt-4o', 'gemma4:31b-cloud']
x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
rects1 = ax.bar(x - width/2, [100.0, 100.0, 100.0], width, label='Schema Validity (%)', color='#2b5c8f')
rects2 = ax.bar(x + width/2, [100.0, 90.0, 100.0], width, label='Logic Consistency Pass Rate (%)', color='#d95f02')

ax.set_ylabel('Tỷ lệ thành công (%)', fontsize=12)
ax.set_title('Đối sánh Tỷ lệ Hợp lệ Cú pháp và Tính Nhất quán Logic (30 Trials)', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=11)
ax.set_ylim(0, 115)
ax.legend(frameon=True, loc='lower right', fontsize=10)

def autolabel(rects, suffix='%'):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}{suffix}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

autolabel(rects1, suffix='%')
autolabel(rects2, suffix='%')
fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/chart_pass_rate.png")
plt.close()

# 2. Latency Comparison Chart (P50 vs P95)
p50 = [10.88, 19.53, 10.73]
p95 = [12.84, 27.12, 19.92]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
rects1 = ax.bar(x - width/2, p50, width, label='Latency P50 (Trung vị, giây)', color='#1b9e77')
rects2 = ax.bar(x + width/2, p95, width, label='Latency P95 (Phân vị 95%, giây)', color='#7570b3')

ax.set_ylabel('Thời gian phản hồi (giây)', fontsize=12)
ax.set_title('Độ trễ Sinh Kịch bản Toàn trình theo Phân vị P50 và P95', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=11)
ax.set_ylim(0, 32)
ax.legend(frameon=True, loc='upper left', fontsize=10)

autolabel(rects1, suffix='s')
autolabel(rects2, suffix='s')
fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/chart_latency.png")
plt.close()

# 3. High level architecture diagram
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
ax.axis('off')

boxes = [
    (0.05, 0.70, 0.90, 0.22, "TẦNG GIAO DIỆN CLIENT (UNITY 6 URP 2D)\n- Bàn điều tra Corkboard 2.5D (ảnh Polaroid, dây chỉ đỏ, đèn bàn tương tác)\n- Modals: Khám nghiệm tử thi Henssge, Vật chứng, Kết án & Phòng Co-op LAN", '#e8f4f8', '#2b5c8f'),
    (0.05, 0.40, 0.90, 0.22, "TẦNG DỊCH VỤ FASTAPI, PYDANTIC V2 & CSDL SQLITE\n- REST API (/api/case/generate, /api/case/verify, /api/cases) & WebSocket Co-op\n- Kiểm chuẩn Pydantic v2, Bộ nhớ đệm & SQLite (SQLAlchemy 2.0 WAL)", '#fef0e7', '#d95f02'),
    (0.05, 0.05, 0.90, 0.28, "TẦNG LÕI NEURO-SYMBOLIC HYBRID ENGINE\n- Neural: Chuỗi 4 Tác tử (OutlineAgent, CharacterAgent, ClueAgent, DeductionAgent)\n- Symbolic: Giải tích Nhiệt Henssge (Bisection) + Đồ thị Hai phía & Kiểm định Ràng buộc\n- Sửa lỗi Cục bộ: Localized Patch Repair O(1) theo Diagnostic Violation", '#eaf7ed', '#1b9e77')
]

for left, bottom, w, h, text, bg, border in boxes:
    rect = plt.Rectangle((left, bottom), w, h, facecolor=bg, edgecolor=border, linewidth=2, transform=ax.transAxes, zorder=2)
    ax.add_patch(rect)
    ax.text(left + w/2, bottom + h/2, text, ha='center', va='center', fontsize=9.5, transform=ax.transAxes, zorder=3, fontweight='bold')

ax.annotate('', xy=(0.5, 0.70), xytext=(0.5, 0.62), arrowprops=dict(facecolor='#333333', arrowstyle='<->', lw=2), zorder=4)
ax.annotate('', xy=(0.5, 0.40), xytext=(0.5, 0.33), arrowprops=dict(facecolor='#333333', arrowstyle='<->', lw=2), zorder=4)

fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/architecture_overview.png")
plt.close()

# 4. Decoupled Flowchart
fig, ax = plt.subplots(figsize=(10.5, 4.5), dpi=300)
ax.axis('off')

steps = [
    (0.01, 0.34, 0.21, 0.34, "1. Client UI gửi\nVerifyRequest\n(POST /api/case/verify)", '#e1eaf2', '#1a365d'),
    (0.26, 0.34, 0.22, 0.34, "2. FastAPI & Pydantic v2\nKiểm chuẩn schema &\nnạp hồ sơ SQLite/Cache", '#e6fffa', '#234e52'),
    (0.52, 0.34, 0.23, 0.34, "3. evaluate_player_deduction\nSo khớp thủ phạm & chứng cứ\nBộ lọc SPAM_DETECTED\n-> VerifyResponse (< 0.1 ms)", '#fff5f5', '#742a2a'),
    (0.79, 0.34, 0.20, 0.34, "4. Lưu vết & Phản hồi\nGhi bảng deduction_logs\nTiết lộ core_contradiction\n(Không dùng LLM phán quyết)", '#eaf7ed', '#1b9e77')
]

for left, bottom, w, h, text, bg, border in steps:
    rect = plt.Rectangle((left, bottom), w, h, facecolor=bg, edgecolor=border, linewidth=1.5, transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(left + w/2, bottom + h/2, text, ha='center', va='center', fontsize=8.0, transform=ax.transAxes, fontweight='bold', linespacing=1.4)

for i in range(len(steps)-1):
    x1 = steps[i][0] + steps[i][2]
    x2 = steps[i+1][0]
    y = 0.34 + 0.34/2
    ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(facecolor='#4a5568', arrowstyle='->', lw=2))

ax.text(0.5, 0.84, "LUỒNG XÁC THỰC KẾT ÁN TẤT ĐỊNH (POST /api/case/verify)\nTÁCH BIỆT KHỎI MÔ HÌNH NGÔN NGỮ XÁC SUẤT", ha='center', va='center', fontsize=11, fontweight='bold', transform=ax.transAxes, color='#1a202c')

fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/decoupled_flowchart.png")
plt.close()
print("All 4 thesis charts generated successfully in figures/")
