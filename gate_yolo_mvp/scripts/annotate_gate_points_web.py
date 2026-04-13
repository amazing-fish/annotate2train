#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path
from typing import List

from flask import Flask, jsonify, request, Response
from PIL import Image

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Gate Annotator Web</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #111; color: #eee; }
    .topbar { padding: 12px 16px; background: #1b1b1b; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    button { padding: 8px 12px; cursor: pointer; }
    .hint { color: #bbb; font-size: 14px; }
    .wrap { padding: 12px 16px; }
    canvas { border: 1px solid #444; max-width: 100%; background: #222; }
    .meta { margin: 10px 0; display:flex; gap:20px; flex-wrap:wrap; }
    .ok { color: #8f8; }
    .warn { color: #ffb347; }
  </style>
</head>
<body>
  <div class="topbar">
    <button onclick="prevImage()">上一张</button>
    <button onclick="resetPoints()">重置</button>
    <button onclick="saveOnly()">保存</button>
    <button onclick="saveAndNext()">保存并下一张</button>
    <button onclick="nextImage()">下一张</button>
    <span id="status" class="hint"></span>
  </div>
  <div class="wrap">
    <div class="meta">
      <div id="meta"></div>
      <div class="hint">点击两次：先 pivot，再 tip。已标注会自动回显。</div>
    </div>
    <canvas id="canvas"></canvas>
  </div>
<script>
let current = null;
let points = [];
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let img = new Image();

function setStatus(msg, cls='hint') {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = cls;
}

async function loadImage(index=null) {
  const url = index === null ? '/api/current' : `/api/current?index=${index}`;
  const res = await fetch(url);
  const data = await res.json();
  current = data;
  points = data.points || [];
  img.onload = () => {
    canvas.width = img.width;
    canvas.height = img.height;
    redraw();
  };
  img.src = data.image_data_url;
  document.getElementById('meta').textContent = `[${data.index + 1}/${data.total}] ${data.image_name}`;
  setStatus(data.ann_exists ? '已加载现有标注' : '未标注', data.ann_exists ? 'ok' : 'warn');
}

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0);
  ctx.lineWidth = 3;
  ctx.font = '20px Arial';

  if (points.length >= 1) {
    drawPoint(points[0][0], points[0][1], '#00ff66', 'pivot');
  }
  if (points.length >= 2) {
    drawPoint(points[1][0], points[1][1], '#ff5050', 'tip');
    ctx.strokeStyle = '#ff00ff';
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    ctx.lineTo(points[1][0], points[1][1]);
    ctx.stroke();
  }
}

function drawPoint(x, y, color, text) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillText(text, x + 8, y - 8);
}

canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = Math.round((e.clientX - rect.left) * scaleX);
  const y = Math.round((e.clientY - rect.top) * scaleY);
  if (points.length >= 2) points = [];
  points.push([x, y]);
  redraw();
});

function resetPoints() {
  points = [];
  redraw();
  setStatus('已重置', 'warn');
}

async function saveOnly() {
  if (points.length !== 2) {
    setStatus('必须标 2 个点：pivot、tip', 'warn');
    return;
  }
  const res = await fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({index: current.index, points})
  });
  const data = await res.json();
  setStatus(data.message, data.ok ? 'ok' : 'warn');
}

async function saveAndNext() {
  await saveOnly();
  if (current.index < current.total - 1) await loadImage(current.index + 1);
}

async function nextImage() {
  if (current.index < current.total - 1) await loadImage(current.index + 1);
}

async function prevImage() {
  if (current.index > 0) await loadImage(current.index - 1);
}

loadImage();
</script>
</body>
</html>'''


def image_to_data_url(path: Path) -> str:
    img = Image.open(path).convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{b64}'


def ann_path(ann_dir: Path, image_path: Path) -> Path:
    return ann_dir / f'{image_path.stem}.json'


def load_points(ann_dir: Path, image_path: Path):
    p = ann_path(ann_dir, image_path)
    if not p.exists():
        return [], False
    with p.open('r', encoding='utf-8') as f:
        data = json.load(f)
    insts = data.get('instances', [])
    if not insts:
        return [], True
    inst = insts[0]
    pivot = inst.get('pivot')
    tip = inst.get('tip')
    if not pivot or not tip:
        return [], True
    return [[int(pivot[0]), int(pivot[1])], [int(tip[0]), int(tip[1])]], True


def save_points(ann_dir: Path, image_path: Path, points: List[List[int]]):
    if len(points) != 2:
        raise ValueError('Need exactly 2 points')
    img = Image.open(image_path)
    w, h = img.size
    pivot, tip = points
    x1, y1 = min(pivot[0], tip[0]), min(pivot[1], tip[1])
    x2, y2 = max(pivot[0], tip[0]), max(pivot[1], tip[1])
    data = {
        'version': 'gate-mvp-1.1-web',
        'image_file': image_path.name,
        'image_width': w,
        'image_height': h,
        'instances': [{
            'id': 1,
            'class_name': 'gate_arm',
            'pivot': [int(pivot[0]), int(pivot[1])],
            'tip': [int(tip[0]), int(tip[1])],
            'bbox_xyxy': [int(x1), int(y1), int(x2), int(y2)],
            'status': 'labeled',
        }]
    }
    out = ann_path(ann_dir, image_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_app(image_dir: Path, ann_dir: Path) -> Flask:
    app = Flask(__name__)
    images = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS])
    if not images:
        raise FileNotFoundError(f'No images found under {image_dir}')

    @app.get('/')
    def index() -> Response:
        return Response(HTML, mimetype='text/html')

    @app.get('/api/current')
    def current():
        idx = int(request.args.get('index', 0))
        idx = max(0, min(idx, len(images) - 1))
        img_path = images[idx]
        points, exists = load_points(ann_dir, img_path)
        return jsonify({
            'index': idx,
            'total': len(images),
            'image_name': img_path.name,
            'image_data_url': image_to_data_url(img_path),
            'points': points,
            'ann_exists': exists,
        })

    @app.post('/api/save')
    def save():
        payload = request.get_json(force=True)
        idx = int(payload['index'])
        idx = max(0, min(idx, len(images) - 1))
        points = payload.get('points', [])
        if len(points) != 2:
            return jsonify({'ok': False, 'message': '必须正好 2 个点'}), 400
        save_points(ann_dir, images[idx], points)
        return jsonify({'ok': True, 'message': f'已保存 {images[idx].name}'})

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--ann-dir', type=Path, required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    app = create_app(args.image_dir, args.ann_dir)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
