let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

export function playAlertSound(severity = 'warning') {
  try {
    const ctx = getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const freqMap = { info: 520, warning: 660, critical: 880, emergency: [880, 660, 880] };
    const freq = freqMap[severity] || 660;

    if (Array.isArray(freq)) {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq[0], ctx.currentTime);
      osc.frequency.setValueAtTime(freq[1], ctx.currentTime + 0.15);
      osc.frequency.setValueAtTime(freq[2], ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } else {
      osc.type = severity === 'emergency' ? 'square' : 'sine';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);

      if (severity === 'critical' || severity === 'emergency') {
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(freq * 1.25, ctx.currentTime + 0.2);
        gain2.gain.setValueAtTime(0.2, ctx.currentTime + 0.2);
        gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
        osc2.start(ctx.currentTime + 0.2);
        osc2.stop(ctx.currentTime + 0.6);
      }
    }
  } catch (e) {
    // Audio not supported
  }
}

export async function requestNotificationPermission() {
  if (!('Notification' in window)) return 'denied';
  if (Notification.permission === 'granted') return 'granted';
  if (Notification.permission === 'denied') return 'denied';
  const result = await Notification.requestPermission();
  return result;
}

export function sendBrowserNotification({ title, message, type }) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;

  const iconMap = {
    critical: '🔴',
    emergency: '🔴',
    warning: '🟡',
    info: '🔵',
    error: '⚫',
  };

  try {
    const notif = new Notification(`${iconMap[type] || '🌧'} ${title}`, {
      body: message,
      icon: '/src/MeghDrishti.png',
      badge: '/src/MeghDrishti.png',
      tag: `meghdrishti-${type}`,
      requireInteraction: type === 'emergency' || type === 'critical',
      silent: true,
    });

    notif.onclick = () => {
      window.focus();
      notif.close();
    };

    setTimeout(() => notif.close(), type === 'emergency' ? 30000 : 10000);
  } catch (e) {
    // Browser notification failed
  }
}
