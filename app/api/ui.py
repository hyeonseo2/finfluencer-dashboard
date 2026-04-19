from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.schemas.schemas import DISCLAIMER

router = APIRouter(tags=["ui"])


_UI_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>핀플루언서 비교 분석 대시보드</title>
  <style>
    :root {
      --bg: #09090b;
      --panel: rgba(24, 24, 27, 0.65);
      --line: rgba(255, 255, 255, 0.1);
      --text: #fafafa;
      --muted: #a1a1aa;
      --accent: #60a5fa;
      --accent-soft: #1e3a8a;
      --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      --radius: 16px;
      --glass-border: 1px solid rgba(255, 255, 255, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background: radial-gradient(circle at 15% 50%, rgba(29, 78, 216, 0.15) 0%, transparent 50%),
                  radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                  var(--bg);
      background-attachment: fixed;
      color: var(--text);
      font-family: 'Inter', Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
      line-height: 1.6;
    }

    a { color: inherit; text-decoration: none; }

    .top {
      position: sticky;
      top: 0;
      z-index: 20;
      padding: 16px 24px;
      background: rgba(9, 9, 11, 0.7);
      border-bottom: var(--glass-border);
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }

    .brand {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 16px;
      text-align: center;
      width: 100%;
      background: linear-gradient(135deg, #60a5fa 0%, #c084fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 30px rgba(96, 165, 250, 0.3);
      transition: transform 0.3s ease;
    }
    
    .brand:hover {
      transform: scale(1.02);
    }

    .nav-row {
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 44px;
    }

    .nav {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
    }

    .top .btn {
      border-radius: 999px;
      border: var(--glass-border);
      background: rgba(255, 255, 255, 0.05);
      color: #e4e4e7;
      padding: 8px 18px;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      backdrop-filter: blur(8px);
    }

    .top .btn:hover {
      transform: translateY(-2px);
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
    }

    .top-search {
      position: absolute;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      align-items: center;
    }

    .top-search input {
      width: 220px;
      min-height: 38px;
      border-radius: 999px;
      border: var(--glass-border);
      background: rgba(0, 0, 0, 0.4);
      color: #ffffff;
      padding: 8px 16px;
      outline: none;
      font-size: 13px;
      transition: all 0.3s ease;
    }

    .top-search input::placeholder { color: #71717a; }

    .top-search input:focus {
      width: 260px;
      border-color: var(--accent);
      background: rgba(0, 0, 0, 0.6);
      box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.15);
    }

    .btn {
      border-radius: 12px;
      border: var(--glass-border);
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
      padding: 10px 16px;
      font-size: 14px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      cursor: pointer;
    }

    .btn:hover {
      transform: translateY(-2px) scale(1.02);
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.12);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    }

    .btn:active {
      transform: translateY(0) scale(0.98);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .btn.icon-only {
      min-width: 38px;
      width: 38px;
      height: 38px;
      padding: 0;
      justify-content: center;
      font-size: 16px;
      border-radius: 50%;
    }

    .container {
      max-width: 1200px;
      margin: 24px auto;
      padding: 0 20px 60px;
      width: 100%;
      display: grid;
      gap: 20px;
    }

    .section { margin: 0; }
    h3 { margin: 0 0 12px; font-size: 18px; font-weight: 700; letter-spacing: -0.02em; }
    h4 { margin: 0; }

    .panel {
      background: var(--panel);
      border: var(--glass-border);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .panel:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
      border-color: rgba(255, 255, 255, 0.15);
    }

    .muted { color: var(--muted); font-size: 13px; }
    .footer {
      color: var(--muted);
      font-size: 13px;
      margin: 16px 0 0;
      text-align: center;
    }

    .toolbar {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }

    .toolbar input,
    .toolbar select {
      min-height: 42px;
      padding: 8px 16px;
      border-radius: 12px;
      border: var(--glass-border);
      background: rgba(0, 0, 0, 0.3);
      color: var(--text);
      font-size: 14px;
      transition: all 0.2s ease;
      outline: none;
    }

    .toolbar input:focus,
    .toolbar select:focus {
      border-color: var(--accent);
      background: rgba(0, 0, 0, 0.5);
      box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
    }

    .filters { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-start; }
    .select-wrap { display: flex; flex-direction: column; gap: 6px; }
    .select-wrap label { font-size: 13px; color: #a1a1aa; font-weight: 600; }

    .topic-toggle-wrap {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-top: 4px;
    }

    .video-feed-controls {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }

    .channel-filter-right {
      margin-left: auto;
    }

    .topic-toggle {
      border: var(--glass-border);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.05);
      color: #d4d4d8;
      padding: 8px 14px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

      cursor: pointer;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
      white-space: nowrap;
    }

    .topic-toggle:hover {
      border-color: rgba(96, 165, 250, 0.4);
      background: rgba(96, 165, 250, 0.1);
      color: #bfdbfe;
    }

    .topic-toggle.active {
      border-color: var(--accent);
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.3));
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .topic-toggle.active::after {
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #93c5fd;
      display: inline-block;
      margin-left: 8px;
      box-shadow: 0 0 6px rgba(147, 197, 253, 0.8);
    }

    .list {
      display: grid;
      gap: 16px;
    }

    .item {
      border: var(--glass-border);
      border-radius: var(--radius);
      padding: 16px;
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(8px);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .item:hover {
      transform: translateY(-4px) scale(1.01);
      border-color: rgba(96, 165, 250, 0.3);
      background: rgba(255, 255, 255, 0.05);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
    }

    .video-item {
      display: grid;
      grid-template-columns: 220px 1fr;
      gap: 20px;
      align-items: start;
    }

    .video-item.channel-list-item {
      display: flex;
      flex-direction: row;
      gap: 12px;
    }

    .video-thumb-wrap {
      width: 220px;
      flex: 0 0 220px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      overflow: hidden;
      border-radius: 12px;
    }

    .video-thumb,
    .video-thumb-fallback {
      width: 100%;
      height: 124px;
      border-radius: 12px;
      border: none;
      object-fit: cover;
      background: rgba(0, 0, 0, 0.5);
      display: block;
      transition: transform 0.4s ease;
    }
    
    .item:hover .video-thumb {
      transform: scale(1.05);
    }

    .video-thumb-fallback {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: #71717a;
      font-size: 13px;
      text-align: center;
    }

    .video-body {
      min-width: 0;
      display: grid;
      gap: 8px;
    }

    .video-meta-row {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: nowrap;
      color: #a1a1aa;
      font-size: 13px;
      min-width: 0;
    }

    .video-meta-row .video-channel {
      margin-right: 4px;
      flex: 0 0 auto;
    }

    .video-meta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #a1a1aa;
      font-size: 13px;
      min-width: 0;
      white-space: nowrap;
    }

    .video-title {
      font-size: 18px;
      line-height: 1.4;
      color: #f4f4f5;
      font-weight: 700;
      min-height: 24px;
      word-break: break-word;
      overflow-wrap: anywhere;
      transition: color 0.2s ease;
    }

    .a.link,
    a.link { color: inherit; text-decoration: none; }
    
    .item:hover .video-title {
      color: #93c5fd;
    }

    .video-channel {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.05);
      padding: 4px 10px 4px 4px;
      border-radius: 999px;
      border: var(--glass-border);
      transition: background 0.2s;
    }
    
    .video-channel:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .video-channel-avatar,
    .video-channel-avatar-fallback {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      flex: 0 0 20px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      color: #a1a1aa;
      font-weight: 700;
    }

    .video-channel-name {
      font-size: 12px;
      font-weight: 600;
      color: #e4e4e7;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      flex: 0 0 8px;
      margin-right: 4px;
      box-shadow: 0 0 8px currentColor;
    }
    .status-done { color: #4ade80; background: currentColor; }
    .status-warn { color: #fbbf24; background: currentColor; }
    .status-error { color: #f87171; background: currentColor; }

    .video-extra {
      color: #d4d4d8;
      font-size: 14px;
      line-height: 1.6;
      margin-top: 4px;
      word-break: keep-all;
    }

    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      color: #94a3b8;
    }

    .video-preview {
      white-space: pre-wrap;
      background: rgba(0, 0, 0, 0.3);
      border: 1px dashed rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      margin-top: 10px;
      padding: 12px;
      font-size: 12px;
      color: #a1a1aa;
      line-height: 1.5;
      max-height: 100px;
      overflow-y: auto;
    }

    .topic-sentiment-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border-radius: 10px;
      border: var(--glass-border);
      padding: 10px 14px;
      margin-bottom: 6px;
      transition: background 0.2s, border-color 0.2s;
    }

    .topic-sentiment-item:hover,
    .topic-sentiment-item.active {
      border-color: rgba(96, 165, 250, 0.4);
      background: rgba(255, 255, 255, 0.05);
    }

    .video-thumb-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 26px;
      align-items: center;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      border: var(--glass-border);
      font-size: 12px;
      font-weight: 600;
      padding: 4px 12px;
      color: #e4e4e7;
      background: rgba(255, 255, 255, 0.05);
      white-space: nowrap;
      transition: all 0.2s ease;
    }
    
    .pill:hover {
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }

    .pill .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      flex: 0 0 8px;
    }

    .stance-pill {
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .stance-pill.positive { background: rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.3); color: #86efac; }
    .stance-pill.active.positive, .stance-pill.positive:hover { box-shadow: 0 0 12px rgba(34, 197, 94, 0.4); }
    
    .stance-pill.neutral { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.15); color: #e2e8f0; }
    .stance-pill.active.neutral, .stance-pill.neutral:hover { box-shadow: 0 0 12px rgba(255, 255, 255, 0.2); }
    
    .stance-pill.negative { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #fca5a5; }
    .stance-pill.active.negative, .stance-pill.negative:hover { box-shadow: 0 0 12px rgba(239, 68, 68, 0.4); }

    .pill--no-summary {
      background: rgba(239, 68, 68, 0.1);
      border-color: rgba(239, 68, 68, 0.2);
      color: #fca5a5;
      font-weight: 600;
    }

    .video-section-more {
      margin-top: 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .video-section-more .muted { font-size: 13px; }

    .video-section-more .btn {
      min-width: 120px;
      justify-content: center;
    }

    .channel-list-item {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .channel-avatar-wrap {
      width: 40px !important;
      flex: 0 0 40px !important;
      max-width: 40px !important;
      min-width: 40px !important;
      height: 40px !important;
      margin-top: 0;
    }

    .channel-avatar {
      width: 40px !important;
      height: 40px !important;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }

    .channel-list-item .video-thumb-wrap {
      width: 34px !important;
      min-width: 34px !important;
      max-width: 34px !important;
      flex: 0 0 34px !important;
      display: block;
    }

    .channel-list-item .video-body {
      min-width: 0;
      flex: 1;
      display: grid;
      gap: 4px;
    }

    .channel-title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1px;
    }

    .channel-actions {
      margin-top: 0;
      display: inline-flex;
      gap: 6px;
    }

    .channel-action-btn {
      border: 1px solid #dce5ee;
      background: #f8fafc;
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all .15s ease;
      color: #0f172a;
    }
    .channel-action-btn:hover { border-color: #9cb5ff; background: #edf3ff; }
    .channel-action-btn:disabled { opacity: 0.55; cursor: not-allowed; }

    .channel-popup-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.52);
      z-index: 60;
      display: none;
      align-items: stretch;
      justify-content: center;
      padding: 20px;
    }

    .channel-popup-overlay.open { display: flex; }

    .channel-popup {
      width: min(980px, 96vw);
      max-height: 92vh;
      background: #fff;
      border-radius: 16px;
      border: 1px solid #d9e3f0;
      box-shadow: 0 24px 60px rgba(15, 23, 42, 0.28);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .channel-popup-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: #f8fbff;
    }

    .channel-popup-title {
      margin: 0;
      font-size: 16px;
      color: #0f172a;
      overflow-wrap: anywhere;
      white-space: normal;
      max-width: calc(100vw - 180px);
    }

    #channelPopupHint {
      white-space: normal;
      overflow-wrap: anywhere;
      line-height: 1.4;
    }

    .channel-popup-close {
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: #fff;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }

    .channel-popup-body {
      padding: 12px;
      flex: 1;
      overflow-y: auto;
    }

    .channel-popup-body .list {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
    }

    .channel-popup-body .video-item {
      width: 100%;
      align-items: start;
    }

    @media (max-width: 900px) {
      .top { padding: 12px 10px 10px; }
      .brand { font-size: 22px; margin-bottom: 10px; }
      .top .btn { padding: 7px 11px; font-size: 11px; }
      .nav-row { min-height: auto; }
      .top-search {
        position: static;
        transform: none;
        width: 100%;
        justify-content: center;
        margin-top: 8px;
      }
      .top-search input { width: min(62vw, 220px); font-size: 12px; }

      .container { margin-top: 8px; padding: 0 10px 28px; }
      .video-item { grid-template-columns: 1fr; }
      .video-thumb-wrap,
      .video-thumb,
      .video-thumb-fallback {
        width: 100%;
        max-width: 100%;
        height: auto;
        aspect-ratio: 16 / 9;
      }
      .video-thumb-wrap { flex: 0 0 auto; }
      .video-title { font-size: 15px; min-height: auto; }
      .channel-popup-body .list { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header class="top">
    <div class="brand">핀플루언서 비교 분석 대시보드</div>
    <div class="nav-row">
      <div class="nav">
        <a class="btn" href="#channels">채널</a>
        <a class="btn" href="#videos">영상 피드</a>
        <a class="btn" href="#topicSentimentSection">토픽 분석 피드</a>
      </div>
      <div class="top-search">
        <input id="query" placeholder="영상 검색 (예: 금리)" />
        <button class="btn" onclick="searchVideos()">검색</button>
      </div>
    </div>
  </header>
  <main class="container">
    <section id="channels" class="section">
      <h3>채널</h3>
      <div class="panel">
        <div id="channelList" class="list" style="margin-top:12px"></div>
      </div>
    </section>

    <section id="videos" class="section">
      <h3>영상 피드</h3>
      <div class="panel">
        <div class="toolbar filters video-feed-controls">
          <div class="select-wrap">
            <div id="topicFilterWrap" class="topic-toggle-wrap"></div>
          </div>
          <div class="select-wrap channel-filter-right">
            <select id="videoChannelFilter" onchange="loadVideos()"><option value="">전체 채널</option></select>
          </div>
        </div>
        <div id="videoList" class="list" style="margin-top:12px"></div>
        <div id="videoListPager" class="toolbar video-section-more"></div>
      </div>
    </section>

    <section id="topicSentimentSection" class="section">
      <h3>토픽 분석 피드</h3>
      <div class="panel">
        <div class="toolbar filters video-feed-controls">
          <div class="select-wrap">
            <div id="topicAnalysisFilterWrap" class="topic-toggle-wrap"></div>
          </div>
        </div>
        <p id="topicAnalysisEmpty" class="muted">표시할 영상이 없습니다.</p>
        <div id="topicAnalysisVideoList" class="list" style="margin-top:12px"></div>
        <div id="topicAnalysisPager" class="toolbar video-section-more"></div>
      </div>
    </section>

    <div id="channelPopup" class="channel-popup-overlay" role="dialog" aria-modal="true" aria-hidden="true" onclick="if (event.target === this) closeChannelVideosPopup();">
    <div class="channel-popup">
      <div class="channel-popup-header">
        <h3 class="channel-popup-title" id="channelPopupTitle">채널 영상 보기</h3>
        <button type="button" class="channel-popup-close" onclick="closeChannelVideosPopup()">닫기 ✕</button>
      </div>
      <div class="channel-popup-body">
        <div class="toolbar" style="margin-bottom: 8px;">
          <span id="channelPopupHint" class="muted"></span>
        </div>
        <div id="channelPopupVideoList" class="list"></div>
      </div>
    </div>
  </div>

  <p class="footer">{DISCLAIMER}</p>
  </main>

  <script>
    async function api(path) {
      try {
        const r = await fetch(path);
        if (!r.ok) {
          const t = await r.text().catch(() => '');
          throw new Error(`${path} ${r.status} ${r.statusText}: ${t}`);
        }
        return await r.json();
      } catch (e) {
        throw e;
      }
    }

    async function refreshHealth() {
      try {
        await api('/health');
      } catch(e) {
      }
    }


    const TOPIC_META = {
      macro: { label: '거시/경제', color: '#6366f1', bg: '#eef2ff', border: '#c7d2fe' },
      real_estate: { label: '부동산', color: '#0891b2', bg: '#ecfeff', border: '#a5f3fc' },
      stocks: { label: '주식', color: '#2563eb', bg: '#dbeafe', border: '#93c5fd' },
      etf: { label: 'ETF', color: '#4f46e5', bg: '#ede9fe', border: '#c4b5fd' },
      crypto: { label: '암호화폐', color: '#db2777', bg: '#fce7f3', border: '#f9a8d4' },
      fx: { label: '환율/FX', color: '#0d9488', bg: '#dffcf2', border: '#86efac' },
      bonds: { label: '채권', color: '#ca8a04', bg: '#fef9c3', border: '#fde047' },
      commodities: { label: '원자재', color: '#a16207', bg: '#fef3c7', border: '#fbbf24' },
      policy: { label: '정책', color: '#475569', bg: '#f1f5f9', border: '#cbd5e1' },
      interest_rate: { label: '금리', color: '#dc2626', bg: '#fee2e2', border: '#fecaca' },
    };

    function topicLabel(t) {
      return (TOPIC_META[t] || {}).label || t;
    }

    function topicDotColor(t) {
      const meta = TOPIC_META[t] || {};
      return meta.color || '#64748b';
    }

    let selectedTopic = '';
    let selectedTopicAnalysis = '';
    const VIDEO_FEED_LIMIT = 3;
    const TOPIC_FEED_LIMIT = 3;
    let videoRows = [];
    let videoPage = 1;
    let topicAnalysisRows = [];
    let topicAnalysisPage = 1;

    function topicStyle(t) {
      const meta = TOPIC_META[t] || {};
      if (!meta.label) {
        return 'background:#eef2ff;border:1px solid #d8e4ff;color:#27364d';
      }
      return `background:${meta.bg};border-color:${meta.border};color:${meta.color}`;
    }

    function renderTopicButtonWrap(containerId, topics, selected, onSelect) {
      const wrap = document.getElementById(containerId);
      if (!wrap) return;
      wrap.innerHTML = '';

      const allBtn = document.createElement('button');
      allBtn.type = 'button';
      allBtn.className = `topic-toggle ${selected === '' ? 'active' : ''}`;
      allBtn.textContent = '전체';
      allBtn.onclick = () => {
        onSelect('');
      };
      wrap.appendChild(allBtn);

      (topics || []).forEach((t) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `topic-toggle ${selected === t ? 'active' : ''}`;
        btn.textContent = topicLabel(t);
        btn.onclick = () => {
          onSelect(t);
        };
        btn.style = topicStyle(t);
        wrap.appendChild(btn);
      });
    }

    function setSelectedTopic(t) {
      selectedTopic = t || '';
      const topicData = document.getElementById('topicFilterWrap').dataset.topics || '[]';
      const topics = JSON.parse(topicData);
      renderTopicButtonWrap('topicFilterWrap', topics, selectedTopic, setSelectedTopic);
      loadVideos();
    }

    function setSelectedTopicAnalysis(t) {
      selectedTopicAnalysis = t || '';
      const topicData = document.getElementById('topicAnalysisFilterWrap').dataset.topics || '[]';
      const topics = JSON.parse(topicData);
      renderTopicButtonWrap('topicAnalysisFilterWrap', topics, selectedTopicAnalysis, setSelectedTopicAnalysis);
      loadTopicAnalysisVideos();
    }
    function clearTopicFilter() {
      setSelectedTopic('');
    }

    function openChannelVideosPopup(channelId, channelName = '') {
      if (!channelId) return;

      const overlay = document.getElementById('channelPopup');
      const title = document.getElementById('channelPopupTitle');
      const hint = document.getElementById('channelPopupHint');
      if (!overlay || !title || !hint) return;

      window.currentPopupChannelId = channelId;
      title.textContent = `${channelName || '채널'} 영상 보기`;
      hint.textContent = '';
      overlay.classList.add('open');

      loadChannelOnlyVideos(channelId);
    }

    function closeChannelVideosPopup() {
      const overlay = document.getElementById('channelPopup');
      if (!overlay) return;
      overlay.classList.remove('open');
      const list = document.getElementById('channelPopupVideoList');
      if (list) list.innerHTML = '';
      window.currentPopupChannelId = '';
    }

    function applyUrlChannelFilter() {
      const sel = document.getElementById('videoChannelFilter');
      if (!sel) return;
      const params = new URLSearchParams(window.location.search);
      const cid = params.get('channel_id') || '';
      if (!cid) return;

      // If channel list isn't loaded yet, retry shortly.
      const tryApply = () => {
        const exists = Array.from(sel.options).some((o) => o.value === cid);
        if (!exists) {
          window.setTimeout(() => {
            if (sel && sel.options.length > 1) {
              if (Array.from(sel.options).some((o) => o.value === cid)) {
                sel.value = cid;
                loadVideos();
              }
            }
          }, 200);
          return;
        }
        sel.value = cid;
        loadVideos();
      };

      if (sel.options.length > 1) {
        sel.value = cid;
        loadVideos();
      } else {
        window.setTimeout(tryApply, 150);
      }
    }

    function escapeHtml(v) {
      return String(v || '')
        .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function buildItem(title, meta, link) {
      const d = document.createElement('div');
      d.className = 'item';
      d.innerHTML = `<h4>${escapeHtml(title)}</h4><div class="muted">${escapeHtml(meta)}</div>${link ? `<div class="mono"><a class="link" href="${link}" target="_blank">${link}</a></div>` : ''}`;
      return d;
    }

    function buildVideoItem(v, highlightTopic = selectedTopic, includeTopicInStanceLabel = true, hideTopicPills = false, showAllTopicStancePills = false) {
      const title = (v.title && String(v.title).trim()) ? v.title : `영상(${v.video_id})`;
      const d = document.createElement('div');
      d.className = 'item video-item';

      const thumbWrap = document.createElement('div');
      thumbWrap.className = 'video-thumb-wrap';
      const thumbLink = document.createElement('a');
      thumbLink.className = 'link';
      thumbLink.href = v.source_url || '#';
      thumbLink.target = '_blank';
      thumbLink.rel = 'noopener noreferrer';
      thumbLink.onclick = (ev) => ev.stopPropagation();

      if (v.thumbnail_url) {
        const img = document.createElement('img');
        img.className = 'video-thumb';
        img.loading = 'lazy';
        img.src = v.thumbnail_url;
        img.alt = title;
        img.referrerPolicy = 'no-referrer';
        img.onerror = () => { img.style.display = 'none'; };
        thumbLink.appendChild(img);
      } else {
        const fb = document.createElement('div');
        fb.className = 'video-thumb-fallback';
        fb.textContent = '썸네일 없음';
        thumbLink.appendChild(fb);
      }
      thumbWrap.appendChild(thumbLink);

      const body = document.createElement('div');
      body.className = 'video-body';
      const h4 = document.createElement('h4');
      h4.className = 'video-title';
      const titleA = document.createElement('a');
      titleA.className = 'link';
      titleA.href = v.source_url || '#';
      titleA.target = '_blank';
      titleA.rel = 'noopener noreferrer';
      titleA.textContent = title;
      titleA.onclick = (ev) => ev.stopPropagation();
      h4.appendChild(titleA);

      const channelWrap = document.createElement('div');
      channelWrap.className = 'video-channel';
      if (v.channel_avatar_url) {
        const av = document.createElement('img');
        av.className = 'video-channel-avatar';
        av.loading = 'lazy';
        av.referrerPolicy = 'no-referrer';
        av.src = v.channel_avatar_url;
        av.alt = v.channel || 'channel';
        av.onerror = () => { av.style.display = 'none'; };
        channelWrap.appendChild(av);
      } else {
        const fb = document.createElement('div');
        fb.className = 'video-channel-avatar-fallback';
        fb.textContent = ((v.channel || '채널').slice(0, 1) || '채');
        channelWrap.appendChild(fb);
      }
      const cn = document.createElement('div');
      cn.className = 'video-channel-name';
      const channelA = document.createElement('a');
      channelA.className = 'link';
      channelA.href = v.channel_id ? `https://www.youtube.com/channel/${v.channel_id}` : '#';
      channelA.target = '_blank';
      channelA.rel = 'noopener noreferrer';
      channelA.textContent = escapeHtml(v.channel);
      channelA.onclick = (ev) => ev.stopPropagation();
      cn.appendChild(channelA);
      channelWrap.appendChild(cn);

      const meta = document.createElement('div');
      meta.className = 'video-meta';
      const statusClass = (v.transcript_status || '').toLowerCase() === 'success' ? 'status-done' : ((v.transcript_status || '').toLowerCase() === 'skipped' ? 'status-warn' : 'status-error');
      const dot = document.createElement('span');
      dot.className = `status-dot ${statusClass}`;
      meta.appendChild(dot);
      const published = document.createElement('span');
      published.textContent = `${fmtDate(v.published_at)} / ${v.transcript_status || 'UNKNOWN'}`;
      meta.appendChild(published);

      const extra = document.createElement('div');
      extra.className = 'video-extra';

      if (v.summary) {
        extra.textContent = `${(v.summary || '').slice(0, 120)}${(v.summary || '').length > 120 ? '...' : ''}`;
      } else if (v.transcript_preview) {
        extra.textContent = '요약 미분석 / 자막 미리보기';
        const preview = document.createElement('div');
        preview.className = 'mono video-preview';
        preview.textContent = `transcript preview:
${v.transcript_preview}`;
        extra.appendChild(preview);
      } else {
        extra.textContent = '요약 미분석';
      }

      const tagsWrap = document.createElement('div');
      tagsWrap.className = 'video-thumb-tags';

      const topics = v.topics || [];
      if (!hideTopicPills && topics.length) {
        topics.forEach(t => {
          const p = document.createElement('span');
          p.className = 'pill';
          p.style.cssText = topicStyle(t);
          const dot = document.createElement('span');
          dot.className = 'dot';
          dot.style.background = topicDotColor(t);
          p.appendChild(dot);
          p.appendChild(document.createTextNode(topicLabel(t)));
          tagsWrap.appendChild(p);
        });
      }

      if (showAllTopicStancePills) {
        const stances = Array.isArray(v.topic_stances) ? v.topic_stances : [];
        stances.forEach((x) => {
          const t = String(x.topic || '').toLowerCase();
          const st = x.stance || 'neutral';
          const p = document.createElement('span');
          p.className = `pill stance-pill ${stanceClass(st)}`;
          p.textContent = `${topicLabel(t)} ${stanceLabel(st)}`;
          tagsWrap.appendChild(p);
        });
      } else {
        const stanceForSelected = (() => {
          if (!highlightTopic) return null;
          const hits = (Array.isArray(v.topic_stances) ? v.topic_stances : []).filter(x => String(x.topic || '').toLowerCase() === String(highlightTopic || '').toLowerCase());
          if (!hits.length) return null;
          return hits[0].stance || 'neutral';
        })();

        if (highlightTopic && stanceForSelected) {
          const p = document.createElement('span');
          p.className = `pill stance-pill ${stanceClass(stanceForSelected)}`;
          p.textContent = includeTopicInStanceLabel
            ? `${topicLabel(highlightTopic)} ${stanceLabel(stanceForSelected)}`
            : `${stanceLabel(stanceForSelected)}`;
          tagsWrap.appendChild(p);
        }
      }

      if (!topics.length) {
        const p = document.createElement('span');
        p.className = 'pill pill--no-summary';
        p.textContent = '의견 미분류';
        tagsWrap.appendChild(p);
      }

      body.appendChild(h4);
      const metaRow = document.createElement('div');
      metaRow.className = 'video-meta-row';
      metaRow.appendChild(channelWrap);
      metaRow.appendChild(meta);
      body.appendChild(metaRow);
      body.appendChild(extra);
      body.appendChild(tagsWrap);
      d.appendChild(thumbWrap);
      d.appendChild(body);
      return d;
    }

    function setPopupModeForChannel(channelId) {
      if (!channelId) return;
      openChannelVideosPopup(channelId);
    }

    async function loadChannelOnlyVideos(channelId) {
      const list = document.getElementById('channelPopupVideoList');
      if (!list) return;
      list.innerHTML = '로딩 중...';
      try {
        const rows = await api(`/videos?channel_id=${encodeURIComponent(channelId)}`);
        list.innerHTML = '';
        if (!rows.length) {
          list.innerHTML = '해당 채널의 영상이 없습니다.';
          return;
        }
        rows.forEach(v => {
          list.appendChild(buildVideoItem(v));
        });
      } catch (e) {
        list.innerHTML = `채널 영상 로드 실패: ${e.message}`;
      }
    }

    async function loadChannels() {
      const list = document.getElementById('channelList');
      const channelSel = document.getElementById('videoChannelFilter');
      list.innerHTML = '로딩 중...';
      try {
        const rows = await api('/channels');
        if (!rows.length) { list.innerHTML = '등록된 채널이 없습니다.'; return; }
        list.innerHTML = '';

        const prevChannel = channelSel ? channelSel.value : '';
        if (channelSel) {
          channelSel.innerHTML = '<option value="">전체 채널</option>';
        }

        rows.forEach((r) => {
          if (channelSel) {
            const opt = document.createElement('option');
            opt.value = r.channel_id;
            opt.textContent = r.display_name;
            if (r.channel_id) { channelSel.appendChild(opt); }
          }

          const item = document.createElement('div');
          item.className = 'video-item channel-list-item';

          const thumbWrap = document.createElement('div');
          thumbWrap.className = 'video-thumb-wrap channel-avatar-wrap';
          const avatarUrl = r.channel_avatar_url || r.avatar_url;
          if (avatarUrl) {
            const img = document.createElement('img');
            img.className = 'channel-avatar';
            img.loading = 'lazy';
            img.referrerPolicy = 'no-referrer';
            img.src = avatarUrl;
            img.alt = r.display_name;
            img.onerror = () => { img.style.display = 'none'; };
            thumbWrap.appendChild(img);
          } else {
            const fb = document.createElement('div');
            fb.className = 'video-channel-avatar-fallback';
            fb.textContent = (r.display_name || '채').slice(0, 1);
            thumbWrap.appendChild(fb);
          }

          const meta = document.createElement('div');
          meta.className = 'video-body';
          const h4 = document.createElement('h4');
          h4.className = 'video-title';
          const a = document.createElement('a');
          a.className = 'link';
          a.href = `https://www.youtube.com/channel/${r.channel_id}`;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.textContent = r.display_name;
          h4.appendChild(a);

          const titleRow = document.createElement('div');
          titleRow.className = 'channel-title-row';
          titleRow.appendChild(h4);

          const actionWrap = document.createElement('div');
          actionWrap.className = 'channel-actions';
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'channel-action-btn';
          btn.textContent = '채널 영상 보기';
          const cid = r.channel_id || '';
          const cname = r.display_name || '채널';
          if (cid) {
            btn.onclick = () => {
              openChannelVideosPopup(cid, cname);
            };
          } else {
            btn.disabled = true;
          }
          actionWrap.appendChild(btn);
          titleRow.appendChild(actionWrap);
          meta.appendChild(titleRow);

          item.appendChild(thumbWrap);
          item.appendChild(meta);
          list.appendChild(item);
        });

        if (channelSel) {
          channelSel.value = prevChannel;
          try {
            loadTopics();
          } catch(_) {}
        }
      } catch (e) {
        list.innerHTML = `채널 목록 로드 실패: ${e.message}`;
      }
    }

    async function loadTopics() {
      const topics = await api('/topics');
      const data = JSON.stringify(topics || []);
      const sortedTopics = [...(topics || [])].sort((a, b) => topicSortKey(a) - topicSortKey(b) || String(a).localeCompare(String(b)));
      const topicWrapA = document.getElementById('topicFilterWrap');
      if (topicWrapA) {
        topicWrapA.dataset.topics = JSON.stringify(sortedTopics);
      }
      const topicWrapB = document.getElementById('topicAnalysisFilterWrap');
      if (topicWrapB) {
        topicWrapB.dataset.topics = JSON.stringify(sortedTopics);
      }
      renderTopicButtonWrap('topicFilterWrap', sortedTopics, selectedTopic, setSelectedTopic);
      renderTopicButtonWrap('topicAnalysisFilterWrap', sortedTopics, selectedTopicAnalysis, setSelectedTopicAnalysis);
    }

    function stanceLabel(stance) {
      const s = String(stance || '').toLowerCase();
      if (s === 'positive' || s === 'bullish' || s === 'dovish') return '긍정';
      if (s === 'negative' || s === 'bearish' || s === 'hawkish') return '부정';
      if (s === 'neutral') return '중립';
      return '보류';
    }

    function stanceClass(stance) {
      const s = String(stance || '').toLowerCase();
      if (s === 'positive' || s === 'bullish' || s === 'dovish') return 'positive';
      if (s === 'negative' || s === 'bearish' || s === 'hawkish') return 'negative';
      return 'neutral';
    }

    function fmtDate(s) {
      if (!s) return '날짜 미확인';
      const d = new Date(s);
      if (Number.isNaN(d.getTime())) return s;
      return d.toLocaleString('ko-KR');
    }

    function topicSortKey(topic) {
      const ordered = ['bonds', 'commodities', 'crypto', 'etf', 'fx', 'interest_rate', 'macro', 'policy', 'real_estate', 'stocks'];
      const idx = ordered.indexOf(topic);
      return idx === -1 ? 999 : idx;
    }

    function renderTopicAnalysisRows() {
      const list = document.getElementById('topicAnalysisVideoList');
      const pager = document.getElementById('topicAnalysisPager');
      const empty = document.getElementById('topicAnalysisEmpty');
      if (!list || !pager || !empty) return;

      list.innerHTML = '';
      pager.innerHTML = '';

      const rows = Array.isArray(topicAnalysisRows) ? topicAnalysisRows : [];
      if (!rows.length) {
        empty.textContent = selectedTopicAnalysis
          ? `${topicLabel(selectedTopicAnalysis)} 토픽 영상이 없습니다.`
          : '표시할 영상이 없습니다.';
        return;
      }

      empty.textContent = '';
      const end = Math.min(rows.length, topicAnalysisPage * TOPIC_FEED_LIMIT);
      rows.slice(0, end).forEach(v => {
        list.appendChild(buildVideoItem(v, selectedTopicAnalysis, true, true, true));
      });

      const hasMore = end < rows.length;
      if (!hasMore) return;

      const line = document.createElement('div');
      line.className = 'muted';
      line.style.padding = '2px 0';
      line.textContent = `${Math.min(end, rows.length)} / ${rows.length}개 표시`;
      pager.appendChild(line);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn icon-only';
      btn.title = `더보기 (${Math.min(TOPIC_FEED_LIMIT, rows.length - end)}개 더)`;
      btn.setAttribute('aria-label', `더보기 ${Math.min(TOPIC_FEED_LIMIT, rows.length - end)}개 더`);
      btn.innerHTML = '↻';
      btn.onclick = () => {
        topicAnalysisPage += 1;
        renderTopicAnalysisRows();
      };
      pager.appendChild(btn);
    }

    async function loadTopicAnalysisVideos() {
      const list = document.getElementById('topicAnalysisVideoList');
      const pager = document.getElementById('topicAnalysisPager');
      const empty = document.getElementById('topicAnalysisEmpty');
      if (!list || !pager || !empty) return;

      list.innerHTML = '';
      pager.innerHTML = '';
      topicAnalysisPage = 1;

      list.innerHTML = '로딩 중...';
      try {
        const path = selectedTopicAnalysis
          ? `/videos?topic=${encodeURIComponent(selectedTopicAnalysis)}`
          : '/videos';
        const rows = await api(path);
        topicAnalysisRows = Array.isArray(rows) ? rows : [];
        renderTopicAnalysisRows();
      } catch (e) {
        list.innerHTML = `토픽 영상 로드 실패: ${e.message}`;
      }
    }

  function renderVideoRows() {
      const list = document.getElementById('videoList');
      const pager = document.getElementById('videoListPager');
      if (!list || !pager) return;

      list.innerHTML = '';
      const rows = Array.isArray(videoRows) ? videoRows : [];
      if (!rows.length) {
        list.innerHTML = '영상이 아직 없습니다.';
        pager.innerHTML = '';
        return;
      }

      const end = Math.min(rows.length, videoPage * VIDEO_FEED_LIMIT);
      rows.slice(0, end).forEach(v => {
        list.appendChild(buildVideoItem(v));
      });

      const hasMore = end < rows.length;
      const hasPrev = videoPage > 1;

      pager.innerHTML = '';
      if (!rows.length || (!hasMore && !hasPrev)) {
        return;
      }

      const line = document.createElement('div');
      line.className = 'muted';
      line.style.padding = '2px 0';
      line.textContent = `${Math.min(end, rows.length)} / ${rows.length}개 표시`;
      pager.appendChild(line);

      const btnWrap = document.createElement('div');
      btnWrap.style.display = 'flex';
      btnWrap.style.gap = '8px';

      if (hasMore) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn icon-only';
        btn.title = `더보기 (${Math.min(VIDEO_FEED_LIMIT, rows.length - end)}개 더)`;
        btn.setAttribute('aria-label', `더보기 ${Math.min(VIDEO_FEED_LIMIT, rows.length - end)}개 더`);
        btn.innerHTML = '↻';
        btn.onclick = () => {
          videoPage += 1;
          renderVideoRows();
      
        };
        btnWrap.appendChild(btn);
      }


      pager.appendChild(btnWrap);
    }

    async function loadVideos() {
      const topic = selectedTopic;
      const channelFilter = document.getElementById('videoChannelFilter').value;
      const params = new URLSearchParams();
      if (topic) { params.set('topic', topic); }
      if (channelFilter) { params.set('channel_id', channelFilter); }
      const q = params.toString() ? `?${params.toString()}` : '';
      const list = document.getElementById('videoList');
      const pager = document.getElementById('videoListPager');
      list.innerHTML = '로딩 중...';
      if (pager) pager.innerHTML = '';
      videoPage = 1;
      try {
        const rows = await api(`/videos${q}`);
        videoRows = Array.isArray(rows) ? rows : [];
        renderVideoRows();
      } catch (e) {
        list.innerHTML = `영상 로드 실패: ${e.message}`;
      }
    }

    async function postWithTimeout(path, opts = {}) {
      const controller = new AbortController();
      const timeoutMs = opts.timeoutMs ?? 120000;
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const r = await fetch(path, {
          ...opts,
          signal: controller.signal,
          headers: {
            'X-Admin-Token': 'dev-admin-token',
            ...(opts.headers || {}),
          },
        });
        if (!r.ok) {
          const t = await r.text().catch(() => '');
          throw new Error(`${r.status}: ${t}`);
        }
        return r.json();
      } finally {
        clearTimeout(timer);
      }
    }

    async function bootstrapSeed(btn = null) {
      const btnEl = btn || (typeof event !== "undefined" ? event?.target : null);
      const btnObj = btnEl;
      const status = document.getElementById('ingestStatus');
      if (btnObj) {
        btnObj.disabled = true;
      }
      if (status) {
        status.textContent = '샘플 채널 동기화 중...';
      }
      try {
        // 1) 채널 시드 동기화(빠르게 끝남)
        const seedData = await postWithTimeout('/admin/bootstrap', { method: 'POST', timeoutMs: 30000 });
        if (status) {
          status.textContent = `샘플 채널 반영 완료: 생성 ${seedData.created || 0}개 / 기존 ${seedData.existed || 0}개`;
        }

        // 2) 최신 영상 수집은 별도 단계로 분리해서 실패 범위를 줄임
        const runData = await postWithTimeout('/admin/run_once', { method: 'POST', timeoutMs: 120000 });
        if (status) {
          status.textContent = `수집 완료: 채널 ${runData.channels_processed || 0}개, 새영상 ${runData.new_videos || 0}개, 처리job ${runData.jobs_processed || 0}개`;
        }

        await loadChannels();
        await loadVideos();
      } catch (e) {
        if (status) {
          status.textContent = '샘플 동기화/수집 실패: ' + e.message + ' (네트워크 안정성/Cloud Run 응답지연을 확인하세요)';
        }
        if (String(e).includes('Failed to fetch') || String(e).includes('AbortError')) {
          console.error('admin request failed', e);
        }
      } finally {
        if (btnObj) {
          btnObj.disabled = false;
        }
      }
    }

    async function runOnceIngest(btn = null) {
      const btnEl = btn || (typeof event !== "undefined" ? event?.target : null);
      const btnObj = btnEl;
      const status = document.getElementById('ingestStatus');
      if (btnObj) {
        btnObj.disabled = true;
      }
      if (status) {
        status.textContent = '수집 시작...';
      }
      try {
        const data = await postWithTimeout('/admin/run_once', { method: 'POST', timeoutMs: 120000 });
        if (status) {
          status.textContent = `완료: 채널 ${data.channels_processed || 0}개, 새영상 ${data.new_videos || 0}개, 처리job ${data.jobs_processed || 0}개`;
        }
        await loadChannels();
        await loadVideos();
      } catch (e) {
        if (status) {
          status.textContent = '수집 실패: ' + e.message;
        }
      } finally {
        if (btnObj) {
          btnObj.disabled = false;
        }
      }
    }

    async function searchVideos() {
      const q = document.getElementById('query').value.trim();
      const list = document.getElementById('videoList');
      const pager = document.getElementById('videoListPager');
      if (!q) {
        await loadVideos();
        return;
      }
      list.innerHTML = '로딩 중...';
      if (pager) pager.innerHTML = '';
      const rows = await api(`/search?q=${encodeURIComponent(q)}`);
      list.innerHTML = '';
      if (!rows.length) { list.innerHTML = '결과가 없습니다.'; return; }
      rows.forEach(v => {
        list.appendChild(buildVideoItem(v));
      });
    }

    function filterItems(listId) {
      const list = document.getElementById(listId);
      const q = (document.getElementById('q-channel').value || '').toLowerCase();
      [...list.children].forEach((el) => {
        const t = el.textContent.toLowerCase();
        el.style.display = t.includes(q) ? '' : 'none';
      });
    }

    loadChannels();
    loadTopics();
    loadVideos();
    loadTopicAnalysisVideos();

    const params = new URLSearchParams(window.location.search);
    const popupChannel = params.get('channel_id');
    if (params.get('popup') === '1' && popupChannel) {
      setPopupModeForChannel(popupChannel);
    } else {
      applyUrlChannelFilter();
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeChannelVideosPopup();
      }
    });
  </script>
</body>
</html>"""


@router.get("/ui", response_class=HTMLResponse)
def ui_home() -> str:
    return _UI_HTML.replace("{DISCLAIMER}", DISCLAIMER)


@router.get("/", response_class=HTMLResponse)
def ui_alias() -> str:
    return _UI_HTML.replace("{DISCLAIMER}", DISCLAIMER)

