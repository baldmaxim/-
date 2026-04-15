// Кладка Хаб — основной JS
// Дата в шапке
document.addEventListener('DOMContentLoaded', function () {
  const dateEl = document.querySelector('.topbar-date');
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('ru-RU', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    });
  }
});
