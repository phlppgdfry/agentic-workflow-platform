// Showcase kit — theme toggle, copy buttons, lightbox. No dependencies.
(function () {
  var root = document.documentElement;
  try { var t = localStorage.getItem('sc-theme'); if (t) root.setAttribute('data-theme', t); } catch (e) {}
  var btn = document.querySelector('.theme');
  if (btn) btn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    var next = cur === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('sc-theme', next); } catch (e) {}
  });
  document.querySelectorAll('.code .copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var txt = b.parentElement.querySelector('pre').innerText;
      (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject()).then(function () {
        b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1400);
      }, function () { b.textContent = 'Select & copy'; });
    });
  });
  var lb = document.createElement('div'); lb.className = 'lightbox'; lb.setAttribute('role', 'dialog');
  lb.innerHTML = '<div><img alt=""><p></p></div>'; document.body.appendChild(lb);
  function close() { lb.classList.remove('open'); }
  lb.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  document.querySelectorAll('[data-zoom]').forEach(function (f) {
    f.addEventListener('click', function () {
      var img = f.querySelector('img'); lb.querySelector('img').src = img.src; lb.querySelector('img').alt = img.alt;
      lb.querySelector('p').textContent = f.getAttribute('data-zoom') || ''; lb.classList.add('open');
    });
  });
})();
