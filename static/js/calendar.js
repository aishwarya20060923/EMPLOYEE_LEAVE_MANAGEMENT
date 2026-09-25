// Interactive Monthly Calendar in Vanilla JavaScript

function initCalendar(containerId, eventsApiUrl, modalId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  let currentDate = new Date();
  let eventsData = [];

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  function fetchAndRender() {
    fetch(eventsApiUrl)
      .then(res => res.json())
      .then(events => {
        eventsData = events;
        render();
      })
      .catch(err => {
        console.error("Calendar event fetch error:", err);
        render();
      });
  }

  function render() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDayIndex = new Date(year, month, 1).getDay(); // 0 is Sunday
    const lastDate = new Date(year, month + 1, 0).getDate();
    const prevMonthLastDate = new Date(year, month, 0).getDate();

    const today = new Date();

    let html = `
      <div class="calendar-controls">
        <div class="calendar-month-title">
          ${monthNames[month]} ${year}
        </div>
        <div style="display: flex; gap: 8px;">
          <button type="button" class="btn btn-outline btn-sm" id="calPrevBtn">← Prev</button>
          <button type="button" class="btn btn-outline btn-sm" id="calTodayBtn">Today</button>
          <button type="button" class="btn btn-outline btn-sm" id="calNextBtn">Next →</button>
        </div>
      </div>

      <div class="calendar-weekdays">
        <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
      </div>

      <div class="calendar-grid">
    `;

    // Previous month filler days
    for (let x = firstDayIndex; x > 0; x--) {
      const dayNum = prevMonthLastDate - x + 1;
      html += `
        <div class="calendar-day-cell other-month">
          <span class="day-number">${dayNum}</span>
        </div>
      `;
    }

    // Days of current month
    for (let i = 1; i <= lastDate; i++) {
      const isToday = (
        i === today.getDate() &&
        month === today.getMonth() &&
        year === today.getFullYear()
      );

      const dayOfWeek = new Date(year, month, i).getDay();
      const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);

      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

      // Find events on this date
      const dayEvents = eventsData.filter(e => {
        return dateStr >= e.start && dateStr <= e.end;
      });

      let eventsHtml = '';
      dayEvents.forEach((ev, idx) => {
        if (idx < 3) {
          eventsHtml += `
            <div class="cal-event-chip" style="background-color: ${ev.color || '#3b82f6'};" title="${ev.title}: ${ev.reason || ''}" data-date="${dateStr}" data-title="${ev.title}" data-desc="${ev.reason || ev.description || ''}">
              ${ev.title}
            </div>
          `;
        } else if (idx === 3) {
          eventsHtml += `<div class="cal-event-chip" style="background-color: #64748b;">+${dayEvents.length - 3} more</div>`;
        }
      });

      html += `
        <div class="calendar-day-cell ${isToday ? 'today' : ''} ${isWeekend ? 'weekend' : ''}" data-date="${dateStr}">
          <span class="day-number">${i}</span>
          ${eventsHtml}
        </div>
      `;
    }

    // Next month filler days to complete grid
    const totalCells = firstDayIndex + lastDate;
    const nextDays = (7 - (totalCells % 7)) % 7;
    for (let j = 1; j <= nextDays; j++) {
      html += `
        <div class="calendar-day-cell other-month">
          <span class="day-number">${j}</span>
        </div>
      `;
    }

    html += `</div>`;
    container.innerHTML = html;

    // Attach event listeners to controls
    document.getElementById('calPrevBtn').addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      render();
    });

    document.getElementById('calNextBtn').addEventListener('click', () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      render();
    });

    document.getElementById('calTodayBtn').addEventListener('click', () => {
      currentDate = new Date();
      render();
    });

    // Event click show details
    container.querySelectorAll('.cal-event-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.stopPropagation();
        const title = chip.dataset.title;
        const desc = chip.dataset.desc;
        const dt = chip.dataset.date;
        alert(`Date: ${dt}\n${title}\n${desc ? 'Details: ' + desc : ''}`);
      });
    });
  }

  fetchAndRender();
}

window.initCalendar = initCalendar;
