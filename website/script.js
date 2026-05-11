// Interface tabs
document.querySelectorAll('.iface-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    document.querySelectorAll('.iface-tab').forEach(t => t.classList.toggle('active', t === tab));
    document.querySelectorAll('.iface-panel').forEach(p => {
      p.classList.toggle('active', p.dataset.panel === target);
    });
  });
});

// Smooth nav scroll offset
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href');
    if (href.length > 1) {
      const el = document.querySelector(href);
      if (el) {
        e.preventDefault();
        const offset = el.getBoundingClientRect().top + window.scrollY - 70;
        window.scrollTo({ top: offset, behavior: 'smooth' });
      }
    }
  });
});

// Reveal-on-scroll
const reveal = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.animation = 'fadeUp 0.6s cubic-bezier(.4,0,.2,1) both';
      reveal.unobserve(e.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.feature, .source, .screenshot, .dl-card, .faq-item').forEach(el => {
  reveal.observe(el);
});