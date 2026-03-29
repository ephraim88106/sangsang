/* =============================================
   생생 정보통 - script.js
   계절 자동 감지 + 파티클 효과 + 검색 기능
   ============================================= */

// ── 1. 계절 감지 ──────────────────────────────
function getSeason() {
  const month = new Date().getMonth() + 1; // 1~12
  if (month >= 3 && month <= 5)  return 'spring';
  if (month >= 6 && month <= 8)  return 'summer';
  if (month >= 9 && month <= 11) return 'autumn';
  return 'winter';
}

const SEASON_LABELS = {
  spring: '🌸 봄',
  summer: '🌊 여름',
  autumn: '🍂 가을',
  winter: '❄️ 겨울'
};

function applySeason() {
  const season = getSeason();
  document.body.classList.add(season);

  // 시즌 뱃지 텍스트 업데이트
  document.querySelectorAll('.season-badge').forEach(el => {
    el.textContent = SEASON_LABELS[season];
  });

  // 파티클 시작
  startParticles(season);
}

// ── 2. 파티클 효과 ────────────────────────────
const PARTICLE_CONFIGS = {
  spring: {
    count: 28,
    emoji: ['🌸', '🌷', '🌼'],
    speedY: [0.6, 1.4],
    speedX: [-0.5, 0.5],
    size: [14, 22],
    sway: true
  },
  summer: {
    count: 18,
    emoji: ['✨', '💧', '🫧'],
    speedY: [0.4, 1.0],
    speedX: [-0.3, 0.3],
    size: [12, 20],
    sway: false
  },
  autumn: {
    count: 24,
    emoji: ['🍂', '🍁', '🌿'],
    speedY: [0.5, 1.2],
    speedX: [-0.6, 0.6],
    size: [14, 22],
    sway: true
  },
  winter: {
    count: 35,
    emoji: ['❄️', '⭐', '✦'],
    speedY: [0.3, 0.8],
    speedX: [-0.2, 0.2],
    size: [10, 18],
    sway: false
  }
};

function startParticles(season) {
  const canvas = document.getElementById('season-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const cfg = PARTICLE_CONFIGS[season];
  let particles = [];
  let animId;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function rand(min, max) {
    return Math.random() * (max - min) + min;
  }

  function createParticle() {
    return {
      x: rand(0, canvas.width),
      y: rand(-60, -10),
      emoji: cfg.emoji[Math.floor(Math.random() * cfg.emoji.length)],
      size: rand(...cfg.size),
      speedY: rand(...cfg.speedY),
      speedX: rand(...cfg.speedX),
      sway: cfg.sway ? rand(-0.3, 0.3) : 0,
      swayAngle: rand(0, Math.PI * 2),
      opacity: rand(0.4, 0.9),
      rotation: rand(0, 360),
      rotSpeed: rand(-1.5, 1.5)
    };
  }

  for (let i = 0; i < cfg.count; i++) {
    const p = createParticle();
    p.y = rand(0, canvas.height); // 시작 시 화면에 퍼뜨림
    particles.push(p);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      p.y += p.speedY;
      p.swayAngle += 0.03;
      p.x += p.speedX + Math.sin(p.swayAngle) * p.sway;
      p.rotation += p.rotSpeed;

      ctx.save();
      ctx.globalAlpha = p.opacity;
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.font = `${p.size}px serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(p.emoji, 0, 0);
      ctx.restore();

      // 화면 밖으로 나가면 재생성
      if (p.y > canvas.height + 30 || p.x < -50 || p.x > canvas.width + 50) {
        Object.assign(p, createParticle());
      }
    });

    animId = requestAnimationFrame(draw);
  }

  draw();
}

// ── 3. 카드 클릭 → 글 페이지 이동 ────────────
function initCardLinks() {
  document.querySelectorAll('.card[data-href]').forEach(card => {
    card.addEventListener('click', () => {
      window.location.href = card.dataset.href;
    });
  });
}

// ── 4. 검색 필터 (posts.html에서 사용) ────────
function initSearch() {
  const input = document.getElementById('search-input');
  if (!input) return;

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    document.querySelectorAll('.card').forEach(card => {
      const text = card.textContent.toLowerCase();
      card.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

// ── 5. 부드러운 페이지 진입 애니메이션 ────────
function initFadeIn() {
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity 0.5s ease';
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.body.style.opacity = '1';
    });
  });
}

// ── 초기화 ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initFadeIn();
  applySeason();
  initCardLinks();
  initSearch();
});