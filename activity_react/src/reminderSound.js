let audioContext = null;

export async function enableReminderSound() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;

  if (AudioContextClass) {
    if (!audioContext) audioContext = new AudioContextClass();
    if (audioContext.state === "suspended") await audioContext.resume();

    // Krótki dźwięk testowy odblokowuje audio po kliknięciu użytkownika.
    playReminderSound("test");
  }

  if (!("Notification" in window)) {
    return "Dźwięk został przygotowany. Ta przeglądarka nie obsługuje powiadomień systemowych.";
  }

  if (Notification.permission === "granted") {
    return "Dźwięk i powiadomienia są gotowe.";
  }

  if (Notification.permission === "denied") {
    return "Dźwięk jest przygotowany, ale powiadomienia są zablokowane w ustawieniach przeglądarki.";
  }

  if (!window.isSecureContext) {
    return "Dźwięk jest przygotowany. Powiadomienia systemowe wymagają HTTPS lub adresu localhost.";
  }

  const permission = await Notification.requestPermission();
  return permission === "granted"
    ? "Dźwięk i powiadomienia są gotowe."
    : "Dźwięk jest przygotowany, ale nie przyznano zgody na powiadomienia.";
}

export async function playReminderSound(kind = "reminder") {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return false;

    if (!audioContext) audioContext = new AudioContextClass();

    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }

    const ctx = audioContext;
    if (ctx.state !== "running") return false;

    const isTest = kind === "test";
    const frequency = kind === "before" ? 1000 : isTest ? 660 : 800;
    const count = isTest ? 1 : 10;
    const start = ctx.currentTime + 0.05;

    for (let i = 0; i < count; i++) {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      const at = start + i * 0.45;

      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(frequency, at);

      gain.gain.setValueAtTime(0.0001, at);
      gain.gain.exponentialRampToValueAtTime(0.22, at + 0.025);
      gain.gain.setValueAtTime(0.22, at + 0.16);
      gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.24);

      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start(at);
      oscillator.stop(at + 0.26);
    }

    return true;
  } catch (error) {
    console.warn("Nie udało się odtworzyć dźwięku przypomnienia:", error);
    return false;
  }
}

export function showReminderNotification(title, body) {
  try {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, { body });
    }
  } catch (error) {
    console.warn("Nie udało się wyświetlić powiadomienia:", error);
  }
}
