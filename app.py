import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import os
import imageio_ffmpeg
import matplotlib
from tempfile import NamedTemporaryFile
import time

# 畫面標題
st.set_page_config(page_title="TraceVis - 多時點樣本遷移動畫", layout="centered")
st.title("🧬 TraceVis: 多時點樣本遷移可視化系統")
st.markdown("上傳你的 PCoA .tsv 檔案，支援任意 Visit 組合之間的遷移動畫")

# 檔案上傳
uploaded_file = st.file_uploader("請上傳 pcoa_transition_ready.tsv 檔案", type=["tsv"])

if uploaded_file is None:
    st.warning("請先上傳檔案。")
    st.stop()

# 讀取資料
df = pd.read_csv(uploaded_file, sep="\t", encoding="ISO-8859-1")

# 讓使用者指定欄位
columns = df.columns.tolist()
visit_col = st.selectbox("請選擇 Visit 欄位", columns)
subject_col = st.selectbox("請選擇 SubjectID 欄位", columns)
pc1_col = st.selectbox("請選擇 PC1 欄位", columns)
pc2_col = st.selectbox("請選擇 PC2 欄位", columns)

# 標準化欄位命名
try:
    df['Visit'] = df[visit_col].astype(str)
    df['SubjectID'] = df[subject_col].astype(str)
    df['PC1'] = df[pc1_col]
    df['PC2'] = df[pc2_col]
except Exception as e:
    st.error(f"❌ 資料欄位錯誤：{e}")
    st.stop()

# 移除缺漏值
df = df.dropna(subset=['Visit', 'SubjectID', 'PC1', 'PC2'])

# 動畫參數
n_frames = st.slider("每段動畫的幀數（越高越平滑）", min_value=5, max_value=100, value=30, step=5)
interval = st.slider("動畫速度（毫秒間隔）", min_value=50, max_value=1000, value=200, step=50)

# 使用者勾選要跑哪些 Visit 組別
all_visits = sorted(df['Visit'].dropna().unique())
selected_visits = st.multiselect("選擇要呈現的 Visit 時點（至少 2 個）", all_visits, default=all_visits)

if len(selected_visits) < 2:
    st.warning("請至少選擇兩個 Visit 作為起點與終點。")
    st.stop()

# Visit 顏色設定
st.subheader("每個 Visit 的顏色設定：")
visit_colors = {}
color_options = list(mcolors.CSS4_COLORS.keys())
def_color_cycle = ['blue', 'green', 'orange', 'red', 'purple']
for i, visit in enumerate(selected_visits):
    default_color = def_color_cycle[i % len(def_color_cycle)]
    visit_colors[visit] = st.selectbox(f"{visit} 顏色：", color_options, index=color_options.index(default_color))

# 選擇 Subject
available_subjects = sorted(df['SubjectID'].unique())
selected_subjects = st.multiselect("選擇要顯示的 SubjectID：", available_subjects, default=available_subjects)
df = df[df['SubjectID'].isin(selected_subjects)]

# 篩出有完整時序的 Subject
grouped = df.groupby('SubjectID')
valid_subjects = []
subject_paths = []
for subject, group in grouped:
    visits = group['Visit'].tolist()
    if all(v in visits for v in selected_visits):
        ordered = group.set_index('Visit').loc[selected_visits][['PC1', 'PC2']].values
        subject_paths.append((subject, ordered))
        valid_subjects.append(subject)

if not subject_paths:
    st.error("⚠ 沒有任何 Subject 同時包含選定的 Visit 階段。")
    st.stop()
else:
    st.success(f"✅ 符合條件的 Subject 數量：{len(subject_paths)}")

# 建立畫布與動畫
fig, ax = plt.subplots(figsize=(8, 6))
trajectories = []
colors = []
labels = []

# 預先建立所有段落的顏色漸層
segment_color_maps = {}
for i in range(len(selected_visits) - 1):
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "cmap", [visit_colors[selected_visits[i]], visit_colors[selected_visits[i+1]]], N=n_frames)
    segment_color_maps[(selected_visits[i], selected_visits[i+1])] = [cmap(j / n_frames) for j in range(n_frames)]

for subject, points in subject_paths:
    path_x, path_y, path_c = [], [], []
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        xs = np.linspace(x0, x1, n_frames)
        ys = np.linspace(y0, y1, n_frames)
        cs = segment_color_maps[(selected_visits[i], selected_visits[i+1])]
        path_x.extend(xs)
        path_y.extend(ys)
        path_c.extend(cs)
    trajectories.append((path_x, path_y))
    colors.append(path_c)
    labels.append(subject)

def init():
    init.scatter_plots = [ax.scatter([], [], s=40) for _ in trajectories]
    init.arrows = [ax.arrow(0, 0, 0, 0, alpha=0) for _ in trajectories]
    init.labels = [ax.text(0, 0, '', fontsize=6, alpha=0) for _ in labels]
    update.scatter_plots = init.scatter_plots
    update.arrows = init.arrows
    update.labels = init.labels
    return ax,

def update(frame):
    ax.set_xlim(df['PC1'].min() - 0.1, df['PC1'].max() + 0.1)
    ax.set_ylim(df['PC2'].min() - 0.1, df['PC2'].max() + 0.1)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")

    segment_index = frame // n_frames
    if segment_index < len(selected_visits) - 1:
        title_segment = f"{selected_visits[segment_index]} ➜ {selected_visits[segment_index + 1]}"
    else:
        title_segment = f"{selected_visits[-2]} ➜ {selected_visits[-1]}"
    ax.set_title(f"PCoA Transition Animation ({title_segment})")

    for i, (xs, ys) in enumerate(trajectories):
        if frame < len(xs):
            update.scatter_plots[i].set_offsets([xs[frame], ys[frame]])
            update.scatter_plots[i].set_color(colors[i][frame])
            update.labels[i].set_position((xs[frame], ys[frame]))
            update.labels[i].set_text(labels[i])
            update.labels[i].set_alpha(0.85)
            if frame > 0:
                dx, dy = xs[frame] - xs[frame-1], ys[frame] - ys[frame-1]
                update.arrows[i].remove()
                update.arrows[i] = ax.arrow(xs[frame-1], ys[frame-1], dx, dy,
                                            head_width=0.01, head_length=0.01,
                                            fc=colors[i][frame], ec=colors[i][frame], alpha=0.4, linewidth=1)
    return ax,

# 動畫儲存模式選擇
st.subheader("動畫儲存模式")
save_mode = st.radio("選擇儲存格式：", ["快速預覽（GIF）", "高畫質輸出（MP4）"])

# 產生動畫與下載
tmp_gif = NamedTemporaryFile(delete=False, suffix=".gif")
from matplotlib.animation import FFMpegWriter

# 設定 ffmpeg 路徑
matplotlib.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()

# 建立 FFMpegWriter
ffmpeg_writer = FFMpegWriter(fps=15)
tmp_mp4 = NamedTemporaryFile(delete=False, suffix=".mp4")
ani = animation.FuncAnimation(fig, update, init_func=init, frames=n_frames * (len(selected_visits) - 1), interval=interval, blit=False)
if save_mode == "快速預覽（GIF）":
    ani.save(tmp_gif.name, writer='pillow', fps=10)
else:
    ani.save(tmp_mp4.name, writer=ffmpeg_writer)
if save_mode == "快速預覽（GIF）":
    st.image(tmp_gif.name, caption="PCoA transition animation", use_container_width=True)
else:
    st.video(tmp_mp4.name)
if save_mode == "快速預覽（GIF）":
    with open(tmp_gif.name, "rb") as f:
        st.download_button("⬇ 下載動畫圖 (GIF)", f, file_name="pcoa_animation_custom.gif", mime="image/gif")
else:
    with open(tmp_mp4.name, "rb") as f:
        st.download_button("⬇ 下載動畫圖 (MP4)", f, file_name="pcoa_animation_custom.mp4", mime="video/mp4")

# 每 50 分鐘自動 refresh 畫面，避免 Streamlit idle 被終止
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 50 * 60:
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()
