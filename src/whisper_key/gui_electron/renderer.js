const canvas = document.getElementById('wave-canvas');
const ctx = canvas.getContext('2d');

const statusLabel = document.getElementById('status-label');
const transcriptionText = document.getElementById('transcription-text');
const capsule = document.querySelector('.capsule');

let phase = 0.0;
let currentAmplitude = 0.05;
let targetAmplitude = 0.05;
let volumeRms = 0.0;
let isAnimating = true;
let speed = 0.1; // Base phase step

function drawCurve(ctx, midY, width, height, phaseOffset, amplitude, scale, lineWidth, opacity) {
  ctx.beginPath();
  ctx.lineWidth = lineWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  // Premium vibrant gradient across the width
  const gradient = ctx.createLinearGradient(0, 0, width, 0);
  gradient.addColorStop(0.0, `rgba(45, 212, 191, 0)`); // Fade in from left
  gradient.addColorStop(0.2, `rgba(45, 212, 191, ${opacity})`); // Teal
  gradient.addColorStop(0.5, `rgba(167, 139, 250, ${opacity})`); // Purple
  gradient.addColorStop(0.8, `rgba(244, 114, 182, ${opacity})`); // Pink
  gradient.addColorStop(1.0, `rgba(244, 114, 182, 0)`); // Fade out to right
  ctx.strokeStyle = gradient;

  const K = 4; // Controls the bell curve width
  const F = 6; // Frequency
  const maxAmplitude = (height / 2) * 0.8;
  
  for (let i = -1; i <= 1; i += 0.02) {
    const x = i;
    // Bell curve attenuation so waves taper off beautifully at the edges
    const envelope = 1.0 / (1.0 + K * x * x);
    // Sine wave
    const y = maxAmplitude * amplitude * scale * Math.sin(F * x - phase + phaseOffset) * envelope;
    
    // Map to canvas
    const cx = ((x + 1) / 2) * width;
    const cy = midY + y;
    
    if (i === -1) {
      ctx.moveTo(cx, cy);
    } else {
      ctx.lineTo(cx, cy);
    }
  }
  ctx.stroke();
}

// 60 FPS Animation loop for Siri Wave
function animateWave() {
  if (!isAnimating) return;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Screen blending makes overlapping waves glow brightly
  ctx.globalCompositeOperation = 'screen';
  
  phase += speed;
  
  // Smoothly lerp amplitude
  currentAmplitude += (targetAmplitude - currentAmplitude) * 0.15;
  
  const width = canvas.width;
  const height = canvas.height;
  const midY = height / 2;
  
  // Draw 5 overlapping curves for depth and complexity
  // params: ctx, midY, width, height, phaseOffset, amplitude, scale, lineWidth, opacity
  drawCurve(ctx, midY, width, height, 0.0, currentAmplitude, 1.0, 3.5, 1.0); // Core main line
  drawCurve(ctx, midY, width, height, -1.0, currentAmplitude, 0.7, 2.0, 0.6); // Medium offset
  drawCurve(ctx, midY, width, height, 1.0, currentAmplitude, 0.6, 1.5, 0.5); // Medium offset 2
  drawCurve(ctx, midY, width, height, -2.5, currentAmplitude, 0.3, 1.0, 0.3); // Far background
  drawCurve(ctx, midY, width, height, 2.5, currentAmplitude, -0.4, 1.0, 0.3); // Far background (flipped)
  
  requestAnimationFrame(animateWave);
}

// Start animation immediately
animateWave();

// Handle messages received from Python backend
window.electronAPI.onMessage((msg) => {
  if (msg.type === 'state') {
    // Reset state classes
    capsule.classList.remove('state-listening', 'state-thinking', 'state-idle');
    statusLabel.classList.remove('text-listening', 'text-thinking', 'text-success');
    
    if (msg.value === 'recording') {
      capsule.classList.add('state-listening');
      statusLabel.classList.add('text-listening');
      statusLabel.textContent = 'Слушаю...';
      
      isAnimating = true;
      targetAmplitude = 0.05; // Base breathing
      speed = 0.1;
      
      // Reset text
      transcriptionText.classList.add('text-placeholder');
      transcriptionText.textContent = 'Говорите, текст появится здесь...';
      
    } else if (msg.value === 'processing') {
      capsule.classList.add('state-thinking');
      statusLabel.classList.add('text-thinking');
      statusLabel.textContent = 'Обработка аудио...';
      
      targetAmplitude = 0.02;
      speed = 0.05; // Slower when thinking
      transcriptionText.classList.add('text-placeholder');
      transcriptionText.textContent = 'Whisper переводит аудиозапись в текст...';
      
    } else if (msg.value === 'idle') {
      capsule.classList.add('state-idle');
      statusLabel.classList.add('text-success');
      statusLabel.textContent = 'Готово!';
      
      targetAmplitude = 0.0;
      setTimeout(() => {
        if (targetAmplitude === 0.0) isAnimating = false;
      }, 500);
    }
  }
  
  else if (msg.type === 'volume') {
    volumeRms = Number(msg.value);
    if (statusLabel.textContent === 'Слушаю...') {
      // Extremely responsive mapping: jump up quickly for voice, base of 0.05
      targetAmplitude = 0.05 + (volumeRms * 15.0);
      if (targetAmplitude > 1.2) targetAmplitude = 1.2;
      
      // Speed up the wave slightly when talking louder for more energy
      speed = 0.1 + (volumeRms * 2.0);
      if (speed > 0.35) speed = 0.35;
    }
  }
  
  else if (msg.type === 'text') {
    const text = msg.value.trim();
    if (text) {
      transcriptionText.classList.remove('text-placeholder');
      transcriptionText.textContent = text.charAt(0).toUpperCase() + text.slice(1);
      const container = transcriptionText.parentElement;
      container.scrollTop = container.scrollHeight;
    }
  }
});
