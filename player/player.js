document.addEventListener('DOMContentLoaded', (event) => {
  const playText = 'Play!';
  const pauseText = 'Pause';
  const bufferText = 'Buffering...';

  const player = document.getElementById('player');
  const control = document.getElementById('play');
  const currentSong = document.getElementById('current-song');
  const nextSong = document.getElementById('next-song');
  let failed = false;

  function toggle() {
    if (player.paused) {
      localStorage.setItem('state', 'play');
      player.src = '/mpd.ogg?' + Date.now();
      setTimeout(() => {
        failed = false;
        player.play().catch(() => {
          failed = true;
          control.textContent = playText;
        });
        player.muted = true;
      }, 0);
    } else {
      localStorage.setItem('state', 'pause');
      player.pause();
    }
  }

  control.addEventListener('click', (e) => {
    e.preventDefault();
    toggle();
  });

  player.addEventListener('pause', () => (control.textContent = playText));
  player.addEventListener('loadstart', () => {
    if (!failed) {
      control.textContent = bufferText;
    }
  });
  player.addEventListener('canplay', () => {
    setTimeout(() => {
      if (!player.paused) {
        player.muted = false;
        control.textContent = pauseText;
      }
    }, 1500);
  });

  if (localStorage.getItem('state') === 'play') {
    control.textContent = bufferText;
    toggle();
  } else {
    control.textContent = playText;
  }

  function getTitle(song) {
    return (song ? song.title : '') || 'unknown';
  }

  function update() {
    fetch('/api/')
      .then((r) => r.json())
      .then((r) => {
        currentSong.textContent = getTitle(r.current_song);
        nextSong.textContent = getTitle(r.next_song);
      });
  }
  update();
  let updateInterval = setInterval(update, 5000);

  let ws = null;
  function connect() {
    if (ws !== null) {
      return;
    }

    let wsOrigin = window.location.origin.replace(/^http(?=s?:\/\/)/, 'ws');
    ws = new WebSocket(wsOrigin + '/api/events');

    ws.onopen = () => {
      if (updateInterval !== null) {
        clearInterval(updateInterval);
        updateInterval = null;
      }
      update();
    };

    ws.onclose = () => {
      if (ws === null) {
        return;
      }

      ws = null;
      setTimeout(connect, 1000);
    };

    ws.onerror = () => {
      if (ws === null) {
        return;
      }

      ws = null;
      update();
      setTimeout(connect, 5000);
    };

    ws.onmessage = (event) => {
      let message = JSON.parse(event.data);
      if (message.action === 'EVENT' && message.event === 'update') {
        update();
      }
    };
  }
  connect();
});
