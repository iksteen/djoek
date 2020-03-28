document.addEventListener('DOMContentLoaded', (event) => {
  let playText = "Play!";
  let pauseText = "Pause";
  let bufferText = "Buffering...";

  let player = document.getElementById("player");
  let control = document.getElementById("play");
  let currentSong = document.getElementById("current-song");
  let nextSong = document.getElementById("next-song");
  let failed = false;

  function toggle() {
    if (player.paused) {
      localStorage.setItem("state", "play");
      player.src = "/mpd.ogg?" + Date.now();
      setTimeout(() => {
        failed = false;
        player.play().catch(() => {
          failed = true;
          control.textContent = playText;
        });
        player.muted = true;
      }, 0);
    } else {
      localStorage.setItem("state", "pause");
      player.pause();
    }
  }

  control.addEventListener("click", (e) => {
    e.preventDefault();
    toggle();
  });

  player.addEventListener("pause", () => (control.textContent = playText));
  player.addEventListener("loadstart", () => {
    if (!failed) {
      control.textContent = bufferText;
    }
  });
  player.addEventListener("canplay", () => {
    setTimeout(() => {
      if (!player.paused) {
        player.muted = false;
        control.textContent = pauseText;
      }
    }, 1500);
  });

  if (localStorage.getItem("state") === "play") {
    control.textContent = bufferText;
    toggle();
  } else {
    control.textContent = playText;
  }

  function getTitle(song) {
    return (song ? song.title : '') || 'unknown';
  }

  function update() {
    fetch("/api/")
      .then((r) => r.json())
      .then((r) => {
        currentSong.textContent = getTitle(r.current_song);
        nextSong.textContent = getTitle(r.next_song);
      });
  }
  update();
  setInterval(update, 1000);
});
