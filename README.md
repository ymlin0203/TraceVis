# 🧬 TraceVis: 多時點樣本遷移可視化系統

**TraceVis** 是一款基於 Streamlit 的互動式工具，用於視覺化受試者樣本在不同 Visit（時間點）之間的 PCoA 遷移軌跡，特別適合應用於微生物組、臨床長期追蹤資料分析與研究。

---

## 🚀 功能特色

- 📂 支援上傳自訂的 `.tsv` PCoA 資料檔案
- 🧭 支援任意組合的 Visit 遷移動畫（不限 V1→V4）
- 🎨 自訂各 Visit 的顏色，呈現流暢漸變動畫
- 👤 選擇特定 SubjectID，專注特定受試者變化
- 🌀 預覽動畫（GIF）與高畫質輸出（MP4）
- ⏱ 可調整動畫幀數與播放速度
- 🔁 自動刷新防止雲端休眠（Streamlit Cloud 專用）

---

## 📁 使用方式

1. 開啟 [TraceVis 線上系統](https://share.streamlit.io/YOUR_USERNAME/TraceVis)
2. 上傳你的 `pcoa_transition_ready.tsv` 檔案（含 `SampleID`, `PC1`, `PC2` 欄位）
3. 選擇你想比較的 Visit 組別（例如 V1→V2→V3）
4. 自訂顏色與顯示受試者
5. 產生動畫並下載（GIF/MP4）

---

## 📊 資料格式說明

| SampleID            | PC1     | PC2     |
|---------------------|---------|---------|
| V1-0001_S1          | 0.0123  | -0.0456 |
| V4-0001_S2          | 0.1032  | -0.0056 |

- `SampleID` 應包含 Visit (`V1`, `V2`, etc.) 與 Subject 編號（如 `-0001`）
- 程式會自動萃取 Visit 與 SubjectID 用於繪圖

---

## 📦 本地部署

```bash
git clone https://github.com/YOUR_USERNAME/TraceVis.git
cd TraceVis
pip install -r requirements.txt
streamlit run app.py
