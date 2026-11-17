import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures", exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

# 1. Henssge Cooling Curves Plot
t = np.linspace(0, 24, 500)
T_ambient = 18.0
T_initial = 37.2

def henssge_temp(t, M, C=1.0):
    k = (1.2815 / ((M * C) ** 0.625)) - 0.0284
    # Henssge two-exponential function
    phi = 1.25 * np.exp(-k * t) - 0.25 * np.exp(-5 * k * t)
    return T_ambient + (T_initial - T_ambient) * phi

fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
ax.plot(t, henssge_temp(t, 50), label='Nạn nhân nhẹ cân (M = 50 kg, k cao)', color='#e41a1c', lw=2.2, linestyle='--')
ax.plot(t, henssge_temp(t, 70), label='Nạn nhân chuẩn (M = 70 kg, k chuẩn)', color='#377eb8', lw=2.5)
ax.plot(t, henssge_temp(t, 90), label='Nạn nhân thừa cân (M = 90 kg, k thấp)', color='#4daf4a', lw=2.2, linestyle='-.')
ax.axhline(T_ambient, color='#999999', linestyle=':', label='Nhiệt độ phòng Tambient = 18°C')

# Highlight temperature plateau
ax.axvspan(0, 2.5, alpha=0.15, color='#feb24c', label='Giai đoạn bình nguyên nhiệt học (Plateau 0-2.5h)')

ax.set_xlabel('Thời gian sau khi tử vong (Post-Mortem Interval - Giờ)', fontsize=11)
ax.set_ylabel('Thân nhiệt trực tràng Tbody (°C)', fontsize=11)
ax.set_title('Đồ thị Hạ Thân nhiệt Thi thể Theo Phương trình Tích phân Hai Hàm mũ Henssge', fontsize=12, fontweight='bold')
ax.set_xlim(0, 24)
ax.set_ylim(16, 38)
ax.legend(frameon=True, loc='upper right', fontsize=9.5)

fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/henssge_curves.png")
plt.close()

# 2. Bipartite Solvability Graph Diagram
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)
ax.axis('off')

# Suspects (Left)
suspects = [
    ("SUSP-01\n(Thủ phạm - Quản gia)", 0.2, 0.75, '#ffcccc', '#cc0000'),
    ("SUSP-02\n(Vô tội - Cháu gái)", 0.2, 0.45, '#e6f2ff', '#0066cc'),
    ("SUSP-03\n(Vô tội - Luật sư)", 0.2, 0.15, '#e6f2ff', '#0066cc')
]

# Evidences (Right)
evidences = [
    ("EV-01: Vé tàu hỏa 20:30\n(Hỗ trợ Alibi SUSP-02)", 0.8, 0.85, '#e6fffa', '#008080'),
    ("EV-02: Dấu giày bùn cỡ 42\n(Nghi binh - Red Herring)", 0.8, 0.60, '#fff0f5', '#c71585'),
    ("EV-03: Biên lai nhà thuốc 21:10\n[CRUCIAL CLUE - BẺ GÃY ALIBI]", 0.8, 0.35, '#ffebcd', '#d2691e'),
    ("EV-04: Cuộc gọi ghi âm 21:40\n(Hỗ trợ Alibi SUSP-03)", 0.8, 0.10, '#e6fffa', '#008080')
]

# Draw nodes
for name, x, y, bg, border in suspects:
    box = dict(boxstyle='round,pad=0.5', facecolor=bg, edgecolor=border, lw=2)
    ax.text(x, y, name, ha='center', va='center', bbox=box, fontsize=9.5, fontweight='bold')

for name, x, y, bg, border in evidences:
    box = dict(boxstyle='square,pad=0.5', facecolor=bg, edgecolor=border, lw=1.8)
    ax.text(x, y, name, ha='center', va='center', bbox=box, fontsize=9, fontweight='bold')

# Draw edges
# Crucial contradiction edge: EV-03 -> SUSP-01
ax.annotate('', xy=(0.33, 0.75), xytext=(0.67, 0.35),
            arrowprops=dict(facecolor='#cc0000', edgecolor='#cc0000', arrowstyle='<->', lw=3, linestyle='-'))
ax.text(0.50, 0.58, "CONTRADICTS ALIBI\n(Bẻ gãy ngoại phạm duy nhất)", ha='center', va='center',
        fontsize=9, color='#cc0000', fontweight='bold', bbox=dict(facecolor='white', edgecolor='#cc0000', boxstyle='round,pad=0.2'))

# Support edge: EV-01 -> SUSP-02
ax.annotate('', xy=(0.33, 0.45), xytext=(0.67, 0.85),
            arrowprops=dict(facecolor='#0066cc', edgecolor='#0066cc', arrowstyle='->', lw=1.5, linestyle='--'))

# Red herring edge: EV-02 -> SUSP-02 & SUSP-01
ax.annotate('', xy=(0.33, 0.45), xytext=(0.67, 0.60),
            arrowprops=dict(facecolor='#c71585', edgecolor='#c71585', arrowstyle='->', lw=1.5, linestyle=':'))
ax.annotate('', xy=(0.33, 0.75), xytext=(0.67, 0.60),
            arrowprops=dict(facecolor='#c71585', edgecolor='#c71585', arrowstyle='->', lw=1.5, linestyle=':'))

# Support edge: EV-04 -> SUSP-03
ax.annotate('', xy=(0.33, 0.15), xytext=(0.67, 0.10),
            arrowprops=dict(facecolor='#0066cc', edgecolor='#0066cc', arrowstyle='->', lw=1.5, linestyle='--'))

# Column titles
ax.text(0.2, 0.96, "TẬP NGHI PHẠM ($V_S$)", ha='center', va='center', fontsize=11, fontweight='bold', color='#1a202c')
ax.text(0.8, 0.96, "TẬP CHỨNG CỨ ($V_E$)", ha='center', va='center', fontsize=11, fontweight='bold', color='#1a202c')

fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/bipartite_graph.png")
plt.close()

# 3. Error Taxonomy Breakdown Pie Chart
fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
labels = [
    'Ảo giác tham chiếu thực thể\n(SCHEMA_ERROR - 55%)',
    'Vi phạm mốc nhiệt học TOD\n(TOD_PHYSICS - 25%)',
    'Thủ phạm alibi không thể phá\n(ALIBI_UNBROKEN - 15%)',
    'Đa thủ phạm / Thiếu thủ phạm\n(MULTIPLE/NO_CULPRIT - 5%)'
]
sizes = [55, 25, 15, 5]
colors = ['#e41a1c', '#377eb8', '#ff7f00', '#984ea3']
explode = (0.08, 0, 0, 0)

wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, autopct='%1.0f%%',
                                  shadow=False, startangle=140, colors=colors,
                                  textprops=dict(fontsize=9))
for at in autotexts:
    at.set_fontweight('bold')
    at.set_color('white')

ax.set_title('Phân loại Phổ biến của Các Lỗi Logic Khi LLM Sinh Tự Do (Error Taxonomy)', fontsize=11, fontweight='bold')
fig.tight_layout()
fig.savefig("d:/Work/Đồ Án Tốt Nghiệp/thesis_latex/figures/error_taxonomy.png")
plt.close()

print("Generated 3 new advanced scientific figures successfully!")
