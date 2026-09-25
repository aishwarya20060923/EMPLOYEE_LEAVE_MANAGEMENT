// Main JavaScript for Employee Leave Management System

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const menuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('appSidebar');

  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });

    document.addEventListener('click', function (e) {
      if (!sidebar.contains(e.target) && !menuBtn.contains(e.target) && sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
      }
    });
  }

  // 2. Alert Dismiss
  document.querySelectorAll('.alert-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // Auto dismiss flash alerts after 6 seconds
  setTimeout(function () {
    document.querySelectorAll('.flash-container .alert').forEach(function (alert) {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 500);
    });
  }, 6000);

  // 3. Generic Modal Handlers
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  };

  document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(function (m) {
        m.classList.remove('active');
      });
    }
  });

  // 4. Smart Leave Calculator (for Apply Leave page)
  const startDateInput = document.getElementById('start_date');
  const endDateInput = document.getElementById('end_date');
  const isHalfDayCheckbox = document.getElementById('is_half_day');
  const halfDayContainer = document.getElementById('half_day_type_container');
  const leaveTypeSelect = document.getElementById('leave_type_id');
  const daysDisplay = document.getElementById('calculated_days_display');
  const daysValueSpan = document.getElementById('calculated_days_val');
  const daysNoteSpan = document.getElementById('calculated_days_note');
  const balanceWarning = document.getElementById('balance_warning');

  function calculateLeaveDays() {
    if (!startDateInput || !endDateInput) return;

    const startVal = startDateInput.value;
    const endVal = endDateInput.value;
    const isHalf = isHalfDayCheckbox ? isHalfDayCheckbox.checked : false;

    if (!startVal || !endVal) {
      if (daysDisplay) daysDisplay.style.display = 'none';
      return;
    }

    if (startVal > endVal) {
      if (daysDisplay) {
        daysDisplay.style.display = 'block';
        daysValueSpan.textContent = '0 days';
        daysNoteSpan.textContent = '⚠️ End date cannot be earlier than start date.';
        daysNoteSpan.style.color = '#ef4444';
      }
      return;
    }

    // Call server API for exact calculations excluding weekends and holidays
    fetch('/employee/api/calculate-days', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        start_date: startVal,
        end_date: endVal,
        is_half_day: isHalf
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.days !== undefined) {
        daysDisplay.style.display = 'block';
        daysValueSpan.textContent = data.days + (data.days === 1 ? ' day' : ' days');
        
        let notes = [];
        if (data.weekends_count > 0) {
          notes.push(`${data.weekends_count} weekend day(s) excluded`);
        }
        if (data.holidays_count > 0) {
          notes.push(`${data.holidays_count} mandatory holiday(s) excluded`);
        }
        
        if (notes.length > 0) {
          daysNoteSpan.textContent = `(${notes.join(', ')})`;
          daysNoteSpan.style.color = '#64748b';
        } else {
          daysNoteSpan.textContent = '';
        }

        // Check against selected leave type balance
        if (leaveTypeSelect && balanceWarning) {
          const selectedOption = leaveTypeSelect.options[leaveTypeSelect.selectedIndex];
          if (selectedOption && selectedOption.dataset.balance !== undefined) {
            const availBalance = parseFloat(selectedOption.dataset.balance);
            if (data.days > availBalance) {
              balanceWarning.style.display = 'block';
              balanceWarning.textContent = `⚠️ Warning: Requested ${data.days} days exceeds your available balance (${availBalance} days).`;
            } else {
              balanceWarning.style.display = 'none';
            }
          }
        }
      }
    })
    .catch(err => console.error('Error calculating leave days:', err));
  }

  if (startDateInput && endDateInput) {
    startDateInput.addEventListener('change', function () {
      if (endDateInput.value && endDateInput.value < this.value) {
        endDateInput.value = this.value;
      }
      calculateLeaveDays();
    });

    endDateInput.addEventListener('change', calculateLeaveDays);

    if (isHalfDayCheckbox) {
      isHalfDayCheckbox.addEventListener('change', function () {
        if (halfDayContainer) {
          halfDayContainer.style.display = this.checked ? 'block' : 'none';
        }
        if (this.checked && startDateInput.value) {
          endDateInput.value = startDateInput.value;
        }
        calculateLeaveDays();
      });
    }

    if (leaveTypeSelect) {
      leaveTypeSelect.addEventListener('change', calculateLeaveDays);
    }
  }

  // 5. Fill Demo Account in Login Form
  window.fillDemoAccount = function (email, password) {
    const emailField = document.getElementById('loginEmail');
    const passwordField = document.getElementById('loginPassword');
    if (emailField && passwordField) {
      emailField.value = email;
      passwordField.value = password;
      emailField.focus();
    }
  };
});
