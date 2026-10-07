# OpenDict — Từ điển Anh–Việt mở / Open English–Vietnamese Dictionary

Từ điển Anh–Việt, Việt–Anh chạy hoàn toàn trên trình duyệt, dựng từ dữ liệu mở.
Không tài khoản, không quảng cáo, dùng được offline.

An offline-capable English–Vietnamese / Vietnamese–English dictionary for learners,
built entirely from open data. No account, no ads.

**Demo:** *(đăng lên GitHub Pages sau khi push — sẽ cập nhật link)*
**Demo:** *(GitHub Pages link after push)*

## Tính năng / Features

- ~40.000 mục từ tiếng Việt → tiếng Anh (Wiktionary tiếng Việt) và hàng chục nghìn
  mục từ tiếng Anh → tiếng Việt (Wiktionary tiếng Anh).
- IPA Anh–Mỹ, phát âm bằng giọng máy (Web Speech API), dạng biến tố
  (went → go), gợi ý chính tả, tìm tiếng Việt không cần gõ dấu.
- CEFR level (A1–C2) và hạng tần suất cho từ phổ biến.
- Đồng nghĩa / trái nghĩa, ví dụ, từ liên quan.
- Lưu từ yêu thích, lịch sử tra cứu (lưu trên máy bạn).
- Giao diện Việt/Anh, sáng/tối, hoạt động offline sau lần tải đầu (service worker).

## Nguồn dữ liệu / Data sources

| Nguồn | Giấy phép |
|---|---|
| English Wiktionary, English entries (Wiktextract, kaikki.org) | CC BY-SA 4.0; GFDL |
| Vietnamese Wiktionary (Wiktextract, kaikki.org) | CC BY-SA 4.0; GFDL |
| ECDICT (frequency ranks + fallback IPA) | MIT |
| CEFR-J Vocabulary Profile 1.5 | Free for research & commercial use; citation required |
| Octanove Vocabulary Profile C1/C2 1.0 | CC BY-SA 4.0 |

Chi tiết attribution và checksum từng file: `pipeline/sources.toml`,
`pipeline/sources.sha256`, và trang Giới thiệu trong app.

## Giấy phép / Licence

- **Mã nguồn web app:** MIT — xem `LICENSE`.
- **Dữ liệu từ điển** (`site/data/`): CC BY-SA 4.0 (ECDICT: MIT).
  Khi dùng lại dữ liệu, hãy giữ attribution như bảng trên.

## Tự dựng lại dữ liệu / Building from source

Yêu cầu: Python 3.10+ (không cần Node hay Rust — web app là file tĩnh).

```
cd pipeline
python3 pdownload.py <url> raw/<file>     # hoặc tải tay các URL trong sources.toml
python3 extract_en.py     # mục từ Anh→Việt (cần raw-en.jsonl.gz, ~3GB)
python3 extract_vi.py     # mục từ Việt→Anh
python3 enrich.py         # gắn CEFR + hạng tần suất + IPA dự phòng
python3 pack.py           # chia shard + index -> site/data/
```

Mở `site/index.html` bằng web server tĩnh (ví dụ `python3 -m http.server` trong
`site/`) — không mở trực tiếp bằng `file://` vì app cần `fetch()`.

Deploy GitHub Pages: trỏ Pages vào thư mục `site/` (branch `main`, folder `/site`)
hoặc copy nội dung `site/` ra root của branch `gh-pages`.
