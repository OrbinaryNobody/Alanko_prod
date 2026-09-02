// Админская интеграция с API

// --- ТАБЫ ---
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const targetBtn = e.target.closest('.tab-btn');
      const tabId = targetBtn ? targetBtn.getAttribute('data-tab') : null;
      if (tabId) {
        handleTabChange(tabId);
      }
    });
  });
  
  // Инициализация при загрузке
  const activeTab = document.querySelector('.tab-btn.active');
  if (activeTab) {
    const tabId = activeTab.getAttribute('data-tab');
    if (tabId) handleTabChange(tabId);
  }
});

function handleTabChange(tabId) {
  if (tabId === 'tab-students' && typeof loadAdminStudents === 'function') loadAdminStudents();
  if (tabId === 'tab-teachers' && typeof loadAdminTeachers === 'function') loadAdminTeachers();
  if (tabId === 'tab-programs' && typeof loadAdminPrograms === 'function') loadAdminPrograms();
  if (tabId === 'tab-consultations' && typeof loadAdminConsultations === 'function') loadAdminConsultations();
  if (tabId === 'tab-calendar' && typeof loadAdminCalendar === 'function') loadAdminCalendar();
  if (tabId === 'tab-achievements' && typeof loadAdminAchievements === 'function') loadAdminAchievements();
  if (tabId === 'tab-subscriptions' && typeof loadAdminSubscriptions === 'function') loadAdminSubscriptions();
}

window.handleTabChange = handleTabChange;

let adminCalendarWeekStart = getAdminCalendarWeekStart(new Date());
let adminCalendarFilter = 'all';
  
function getAdminCalendarWeekStart(value) {
  const result = new Date(value);
  const day = result.getDay();
  result.setDate(result.getDate() - (day === 0 ? 6 : day - 1));
  result.setHours(0, 0, 0, 0);
  return result;
}

function formatCalendarDate(value) {
  const y = value.getFullYear();
  const m = String(value.getMonth() + 1).padStart(2, '0');
  const d = String(value.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function escapeCalendarText(value) {
  return String(value || '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[character]));
}

function formatCalendarEventDate(value) {
  if (typeof value === 'string' && value.includes('T')) {
    const [dPart] = value.split('T');
    const [y, m, d] = dPart.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    return dateObj.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
  }
  return new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
}

function formatCalendarEventTime(value) {
  if (typeof value === 'string' && value.includes('T')) {
    const [, tPart] = value.split('T');
    const parts = tPart.split(':');
    return `${parts[0]}:${parts[1]}`;
  }
  return new Date(value).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

window.loadAdminCalendar = async function() {
  const container = document.getElementById('adminCalendarEvents');
  if (!container) return;
  const dateFrom = formatCalendarDate(adminCalendarWeekStart);
  const dateToValue = new Date(adminCalendarWeekStart);
  dateToValue.setDate(dateToValue.getDate() + 6);
  const dateTo = formatCalendarDate(dateToValue);
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted); text-align: center;"><iconify-icon icon="solar:spinner-bold" class="spin"></iconify-icon> Загрузка календаря...</div>';
  try {
    const response = await requestJson(`/calendar/events?date_from=${dateFrom}&date_to=${dateTo}`);
    renderAdminCalendar(response.items || response.data || []);
  } catch (error) {
    container.innerHTML = `<div style="padding: 32px; color: var(--pal-accent-red);">Не удалось загрузить календарь: ${escapeCalendarText(error.message)}</div>`;
  }
};

function renderAdminCalendar(events) {
  const container = document.getElementById('adminCalendarEvents');
  const label = document.getElementById('calendarWeekLabel');
  if (!container) return;
  const weekEnd = new Date(adminCalendarWeekStart);
  weekEnd.setDate(weekEnd.getDate() + 6);
  if (label) label.textContent = `${adminCalendarWeekStart.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long' })} - ${weekEnd.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })}`;
  const filtered = adminCalendarFilter === 'all' ? events : events.filter(event => event.type === adminCalendarFilter);
  if (!filtered.length) {
    container.innerHTML = '<div style="text-align: center; padding: 60px 0; color: var(--text-muted);"><iconify-icon icon="solar:calendar-minimalistic-bold-duotone" style="font-size: 2.5rem; display: block; margin-bottom: 8px; opacity: 0.5;"></iconify-icon>Событий на этой неделе нет.</div>';
    return;
  }
  container.innerHTML = filtered.map(event => {
    const typeLabel = event.type === 'consultation' ? 'Консультация' : 'Занятие';
    const tagClass = event.type === 'consultation' ? 'tag-class' : 'tag-class';
    let dayNum = '01';
    let monthStr = 'Сен';
    if (typeof event.start_at === 'string' && event.start_at.includes('T')) {
      const [dPart] = event.start_at.split('T');
      const [y, m, d] = dPart.split('-').map(Number);
      const dateObj = new Date(y, m - 1, d);
      dayNum = String(d).padStart(2, '0');
      monthStr = dateObj.toLocaleDateString('ru-RU', { month: 'short' });
    } else {
      const eventDate = new Date(event.start_at);
      dayNum = String(eventDate.getDate()).padStart(2, '0');
      monthStr = eventDate.toLocaleDateString('ru-RU', { month: 'short' });
    }
    const timeStr = `${escapeCalendarText(formatCalendarEventTime(event.start_at))} - ${escapeCalendarText(formatCalendarEventTime(event.end_at))}`;
    return `<div class="agenda-item">
      <div class="agenda-date"><span class="agenda-day">${dayNum}</span><span class="agenda-month">${escapeCalendarText(monthStr)}</span></div>
      <div class="agenda-timeline"><div class="agenda-dot pulse"></div><div class="agenda-line"></div></div>
      <div class="agenda-card">
        <div class="agenda-card-header"><span class="agenda-time"><iconify-icon icon="solar:clock-circle-bold-duotone"></iconify-icon> ${timeStr}</span><span class="tag-sm ${tagClass}">${typeLabel}</span></div>
        <h4 class="agenda-title">${escapeCalendarText(event.title)}</h4>
        <p class="agenda-desc">${event.status === 'CANCELLED' ? 'Отменено' : (event.description || (event.type === 'consultation' ? 'Индивидуальная консультация' : `Групповое занятие • ${event.teacher_name || 'Преподаватель'} • ${event.room || 'Зал 1'}`))}</p>
      </div>
    </div>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('calendarPreviousWeek')?.addEventListener('click', () => {
    adminCalendarWeekStart.setDate(adminCalendarWeekStart.getDate() - 7);
    loadAdminCalendar();
  });
  document.getElementById('calendarNextWeek')?.addEventListener('click', () => {
    adminCalendarWeekStart.setDate(adminCalendarWeekStart.getDate() + 7);
    loadAdminCalendar();
  });
  document.querySelectorAll('[data-calendar-filter]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-calendar-filter]').forEach(item => item.classList.remove('active'));
      button.classList.add('active');
      adminCalendarFilter = button.dataset.calendarFilter;
      loadAdminCalendar();
    });
  });
});

function renderProgramGroups(card, program, groups) {
  const groupsList = card.querySelector('.groups-list');
  groupsList.innerHTML = '';
  const programGroups = groups.filter(group => Number(group.program_id) === Number(program.id));

  if (!programGroups.length) {
    const empty = document.createElement('div');
    empty.className = 'group-row';
    empty.innerHTML = `
      <div class="group-info">
        <div class="group-name">У этой программы пока нет групп</div>
        <div class="group-students">Создайте первую группу и привяжите её к программе.</div>
      </div>
      <button class="btn-sm primary create-program-group" type="button">
        <iconify-icon icon="solar:add-circle-bold"></iconify-icon> Создать группу
      </button>`;
    empty.querySelector('.create-program-group').onclick = () => createProgramGroup(card, program);
    groupsList.appendChild(empty);
    return;
  }

  programGroups.forEach(group => {
    const row = document.createElement('div');
    row.className = 'group-row';
    const studentCount = group.student_count !== undefined ? group.student_count : (Array.isArray(group.students) ? group.students.length : 0);
    const scheduleInfo = (group.days && group.time) ? `${group.days} • ${group.time}` : (group.days || group.time || 'Расписание не задано');
    row.innerHTML = `
      <div class="group-info">
        <div class="group-name"></div>
        <div class="group-students">${studentCount} учеников • ${escapeCalendarText(scheduleInfo)}</div>
      </div>
      <div class="dir-actions">
        <button type="button" class="btn-sm primary group-journal-btn"><iconify-icon icon="solar:notebook-bold"></iconify-icon> Журнал</button>
        <button type="button" class="btn-sm group-edit-btn"><iconify-icon icon="solar:pen-bold"></iconify-icon> Изменить</button>
      </div>`;
    row.querySelector('.group-name').textContent = group.title || 'Без названия';
    row.onclick = () => window.openGroupManageModal?.(group.id, group.title || '');
    row.querySelector('.group-journal-btn').onclick = (event) => {
      event.stopPropagation();
      window.openJournalModal?.(group.id, group.title || '');
    };
    row.querySelector('.group-edit-btn').onclick = (event) => {
      event.stopPropagation();
      window.openGroupManageModal?.(group.id, group.title || '');
    };
    groupsList.appendChild(row);
  });
  const addRow = document.createElement('div');
  addRow.className = 'group-row';
  addRow.innerHTML = '<button class="btn-sm primary create-program-group" type="button"><iconify-icon icon="solar:add-circle-bold"></iconify-icon> Создать группу</button>';
  addRow.querySelector('.create-program-group').onclick = () => createProgramGroup(card, program);
  groupsList.appendChild(addRow);
}

async function createProgramGroup(card, program) {
  const title = window.showPrompt ? await window.showPrompt({
    title: 'Создание группы',
    message: `Укажите название группы для программы «${program.title}»:`,
    placeholder: 'Например: Hip-Hop Juniors',
    required: true,
  }) : window.prompt(`Название группы для программы «${program.title}»:`);
  if (!title || !title.trim()) return;
  try {
    await requestJson('/education/groups', {
      method: 'POST',
      body: JSON.stringify({ title: title.trim(), description: null, program_id: program.id }),
    });
    const groupsResponse = await requestJson('/education/groups');
    renderProgramGroups(card, program, groupsResponse.data || []);
    if (window.showToast) {
      window.showToast('Группа успешно создана', 'success');
    }
  } catch (error) {
    if (window.showToast) {
      window.showToast(`Не удалось создать группу: ${error.message}`, 'error');
    } else {
      alert(`Не удалось создать группу: ${error.message}`);
    }
  }
}

// --- УЧЕНИКИ ---
window._adminStudentsList = [];

window.getStudentImageUrl = function(student) {
  if (!student) return null;
  const rawUrl = student.image_url || student.avatar_url || student.image || 
                 student.student_profile?.image_url || student.student_profile?.avatar_url || 
                 student.photo_url || student.photo || student.avatar;
  if (!rawUrl || typeof rawUrl !== 'string' || !rawUrl.trim()) return null;
  const trimmed = rawUrl.trim();

  // Если URL абсолютный http(s) или data/blob
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('data:') || trimmed.startsWith('blob:')) {
    return trimmed;
  }

  const apiBase = window.ALANKO_API_URL || 'http://localhost:8000/api';
  const origin = apiBase.replace(/\/api\/?$/, '');

  // Если относительный путь со слэшем
  if (trimmed.startsWith('/')) {
    return `${origin}${trimmed}`;
  }

  // Если относительный путь без слэша
  return `${origin}/${trimmed}`;
};

window.loadAdminStudents = async function() {
  const container = document.getElementById('adminStudentsList') || document.querySelector('#tab-students .directory-list');
  if (!container) return;
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Загрузка учеников...</div>';
  
  try {
    const res = await apiFetch('/education/students');
    const payload = await res.json();
    const students = payload.data || [];
    window._adminStudentsList = students;
    
    if (!students.length) {
      container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Учеников пока нет.</div>';
      return;
    }
    
    container.innerHTML = students.map((st, index) => {
      const studentName = st.full_name || `${st.first_name || ''} ${st.last_name || ''}`.trim() || st.email || 'Ученик';
      const fallbackUrl = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(studentName) + '&background=2C473E&color=B0D182';
      const imageUrl = window.getStudentImageUrl(st) || fallbackUrl;
      const groupsText = st.groups?.map(g => g.title).join(', ') || 'Без группы';
      const ageText = st.birth_year ? `${new Date().getFullYear() - st.birth_year} лет` : '';
      const metaText = [groupsText, ageText].filter(Boolean).join(' • ');

      return `
      <div class="directory-row" onclick="openStudentDossierByIndex(${index})">
        <div class="dir-identity">
          <div class="dir-avatar">
            <img src="${imageUrl}" alt="${studentName.replace(/"/g, '&quot;')}" loading="lazy" onerror="this.onerror=null; this.src='${fallbackUrl}'">
          </div>
          <div class="dir-info">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <span class="dir-name" style="line-height: 1;">${studentName}</span>
              ${st.email ? `<span style="font-size: 0.72rem; color: var(--text-muted);">${st.email}</span>` : ''}
            </div>
            <span class="dir-meta">${metaText}</span>
          </div>
        </div>
        <div class="dir-stats">
          <div class="dir-stat-item" title="Баллы за задания"><iconify-icon icon="solar:star-circle-bold-duotone" style="color: var(--pal-light-green);"></iconify-icon> ${st.rating_points || 0} баллов</div>
          <div class="dir-stat-item" title="Место в группе"><iconify-icon icon="solar:ranking-bold-duotone" style="color: var(--text-muted);"></iconify-icon> ${st.groups?.length ? st.groups.map(group => `${group.title}: #${group.rank || '-'}`).join(' · ') : 'Место не определено'}</div>
          <div class="dir-stat-item" title="Статус абонемента"><iconify-icon icon="solar:wallet-money-bold-duotone" style="color: ${st.payment_status === 'PAID' ? 'var(--pal-light-green)' : '#EF6C6C'};"></iconify-icon> ${st.payment_status === 'PAID' ? 'Оплачено' : st.payment_status === 'NO_SUBSCRIPTION' ? 'Нет абонемента' : 'Не оплачено'}</div>
        </div>
        <div class="dir-actions">
          <button class="btn-icon-danger" onclick="event.stopPropagation(); deleteStudentAdmin(${st.id})" style="padding: 8px;" title="Удалить ученика">
            <iconify-icon icon="solar:trash-bin-trash-bold"></iconify-icon>
          </button>
        </div>
      </div>
    `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div style="padding: 32px; color: red;">Ошибка: ${err.message}</div>`;
  }
};

window.openStudentDossierByIndex = function(index) {
  const student = window._adminStudentsList[index];
  if (!student) return;
  if (typeof window.openStudentDossier === 'function') {
    window.openStudentDossier(student);
  }
};

window.deleteStudentAdmin = async function(id) {
  const confirmed = window.showConfirm ? await window.showConfirm({
    title: 'Удалить ученика?',
    message: 'Профиль ученика и все данные будут удалены безвозвратно.',
    type: 'danger',
    confirmText: 'Да, удалить',
    cancelText: 'Отмена'
  }) : confirm('Удалить ученика?');
  if (!confirmed) return;
  try {
    const res = await apiFetch(`/accounts/students/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Ошибка удаления');
    if (window.showToast) {
      window.showToast('Ученик успешно удален', 'success');
    }
    loadAdminStudents();
  } catch (err) {
    if (window.showToast) {
      window.showToast(err.message, 'error');
    } else {
      alert(err.message);
    }
  }
};

window.resetStudentPhotoPreview = function() {
  const input = document.getElementById('studentImageUpload') || document.querySelector('#newStudentForm [name="image"]');
  if (input) input.value = '';
  const placeholder = document.getElementById('studentUploadPlaceholder');
  const previewContainer = document.getElementById('studentPreviewContainer');
  const previewImg = document.getElementById('studentImagePreviewImg');
  const fileNameSpan = document.getElementById('studentImageFileName');
  const dropArea = document.getElementById('studentDropArea') || input?.closest('.file-drop-area');

  if (previewImg) previewImg.src = '';
  if (fileNameSpan) fileNameSpan.textContent = '';
  if (placeholder) placeholder.style.display = 'flex';
  if (previewContainer) previewContainer.style.display = 'none';
  if (dropArea) {
    dropArea.style.borderColor = 'var(--card-border)';
    dropArea.style.background = '';
  }
};

window.saveNewStudent = async function(event) {
  event?.preventDefault();
  const form = document.getElementById('newStudentForm');
  if (!form || !form.reportValidity()) return;

  const button = document.querySelector('#addNewStudentModal .modal-header .btn-primary');
  const originalContent = button ? button.innerHTML : 'Создать профиль';
  if (button) {
    button.disabled = true;
    button.textContent = 'Создание...';
  }

  try {
    const formData = new FormData(form);
    
    // Если файл не выбран или пустой, удаляем ключ чтобы не слать пустой multipart файл
    const imageInput = form.querySelector('[name="image"]');
    const imageFile = imageInput?.files?.[0];
    if (!imageFile || imageFile.size === 0) {
      formData.delete('image');
    }

    const response = await requestFormData('/accounts/students', formData, { method: 'POST' });
    form.reset();
    window.resetStudentPhotoPreview();
    if (typeof closeModal === 'function') {
      closeModal('addNewStudentModal');
    }
    await loadAdminStudents();
    const studentName = response?.data?.email || response?.email || form.querySelector('[name="email"]')?.value || '';
    if (window.showToast) {
      window.showToast(`Ученик успешно создан: ${studentName}`, 'success');
    } else {
      alert(`Ученик успешно создан: ${studentName}`);
    }
  } catch (error) {
    if (window.showToast) {
      window.showToast(`Не удалось создать ученика: ${error.message}`, 'error');
    } else {
      alert(`Не удалось создать ученика: ${error.message}`);
    }
  } finally {
    if (button) {
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }
};

function initializeStudentImagePreview() {
  const input = document.getElementById('studentImageUpload') || document.querySelector('#newStudentForm [name="image"]');
  const dropArea = document.getElementById('studentDropArea') || input?.closest('.file-drop-area');
  const placeholder = document.getElementById('studentUploadPlaceholder');
  const previewContainer = document.getElementById('studentPreviewContainer');
  const previewImg = document.getElementById('studentImagePreviewImg');
  const fileNameSpan = document.getElementById('studentImageFileName');
  const removeBtn = document.getElementById('removeStudentPhotoBtn');

  if (!input || !dropArea) return;
  if (dropArea.dataset.previewInitialized === 'true') return;
  dropArea.dataset.previewInitialized = 'true';

  function showFilePreview(file) {
    if (!file) return;
    const isImg = (file.type && file.type.startsWith('image/')) || /\.(jpe?g|png|webp|gif|svg|bmp|heic)$/i.test(file.name || '');
    if (!isImg) {
      if (window.showToast) {
        window.showToast('Пожалуйста, выберите файл изображения (JPG, PNG, WebP).', 'warning');
      } else {
        alert('Пожалуйста, выберите файл изображения (JPG, PNG, WebP).');
      }
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      if (previewImg) previewImg.src = e.target.result;
      if (fileNameSpan) {
        const sizeKb = Math.round(file.size / 1024);
        fileNameSpan.textContent = `${file.name} (${sizeKb} КБ)`;
      }
      if (placeholder) placeholder.style.display = 'none';
      if (previewContainer) previewContainer.style.display = 'flex';
      dropArea.style.borderColor = 'var(--pal-light-green)';
      dropArea.style.background = 'rgba(176, 209, 130, 0.05)';
    };
    reader.readAsDataURL(file);
  }

  window.previewStudentImage = showFilePreview;

  // Остановка всплытия клика с инпута, чтобы избежать циклов
  input.addEventListener('click', (e) => {
    e.stopPropagation();
  });

  // Клик по дроп-зоне
  dropArea.addEventListener('click', (e) => {
    if (e.target === input) return;
    if (e.target.closest('#removeStudentPhotoBtn') || e.target.closest('button')) return;
    input.click();
  });

  // Изменение файла через стандартный input
  input.addEventListener('change', () => {
    const file = input.files?.[0];
    if (file) {
      showFilePreview(file);
    } else {
      window.resetStudentPhotoPreview();
    }
  });

  // Кнопка удаления фото
  if (removeBtn) {
    removeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      window.resetStudentPhotoPreview();
    });
  }

  // Drag & Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.style.borderColor = 'var(--pal-light-green)';
      dropArea.style.background = 'rgba(176, 209, 130, 0.12)';
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!input.files?.length) {
        dropArea.style.borderColor = 'var(--card-border)';
        dropArea.style.background = '';
      } else {
        dropArea.style.borderColor = 'var(--pal-light-green)';
        dropArea.style.background = 'rgba(176, 209, 130, 0.05)';
      }
    });
  });

  dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const dt = e.dataTransfer;
    const file = dt?.files?.[0];
    if (file) {
      try {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        input.files = dataTransfer.files;
      } catch (err) {
        console.warn('DataTransfer files assignment:', err);
      }
      showFilePreview(file);
    }
  });

  // Инициализация превью для досье (когда меняется фото в карточке досье)
  const dossierFileInput = document.getElementById('dossierImageUpload');
  if (dossierFileInput && !dossierFileInput.dataset.previewInitialized) {
    dossierFileInput.dataset.previewInitialized = 'true';
    dossierFileInput.addEventListener('change', () => {
      const f = dossierFileInput.files?.[0];
      if (f) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const dossierPhoto = document.querySelector('#studentDossierModal .dossier-photo-large');
          if (dossierPhoto) dossierPhoto.src = e.target.result;
        };
        reader.readAsDataURL(f);
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeStudentImagePreview);
} else {
  initializeStudentImagePreview();
}

window.saveNewTeacher = async function(event) {
  event?.preventDefault();
  const form = document.getElementById('newTeacherForm');
  if (!form || !form.reportValidity()) return;

  const formData = new FormData(form);
  if (!form.querySelector('[name="image"]')?.files?.[0]) formData.delete('image');

  const button = document.querySelector('#addNewTeacherModal .modal-header .btn-primary');
  const originalContent = button.innerHTML;
  button.disabled = true;
  button.textContent = 'Создание...';
  try {
    const response = await requestFormData('/accounts/teachers', formData, { method: 'POST' });
    form.reset();
    resetTeacherPhotoPreview();
    closeModal('addNewTeacherModal');
    await loadAdminTeachers();
    const generatedPassword = response?.data?.password;
    window.showToast?.(generatedPassword ? `Преподаватель создан. Пароль: ${generatedPassword}` : 'Преподаватель успешно создан', 'success');
  } catch (error) {
    if (window.showToast) {
      window.showToast(`Не удалось создать преподавателя: ${error.message}`, 'error');
    } else {
      alert(`Не удалось создать преподавателя: ${error.message}`);
    }
  } finally {
    button.disabled = false;
    button.innerHTML = originalContent;
  }
};

window.resetTeacherPhotoPreview = function() {
  const input = document.getElementById('teacherImageUpload');
  const placeholder = document.getElementById('teacherUploadPlaceholder');
  const preview = document.getElementById('teacherPreviewContainer');
  const image = document.getElementById('teacherImagePreviewImg');
  const fileName = document.getElementById('teacherImageFileName');
  if (input) input.value = '';
  if (image) image.src = '';
  if (fileName) fileName.textContent = '';
  if (placeholder) placeholder.style.display = 'flex';
  if (preview) preview.style.display = 'none';
};

function initializeTeacherImagePreview() {
  const input = document.getElementById('teacherImageUpload');
  const dropArea = document.getElementById('teacherDropArea');
  if (!input || !dropArea || dropArea.dataset.previewInitialized === 'true') return;
  dropArea.dataset.previewInitialized = 'true';
  const showPreview = (file) => {
    if (!file) return;
    if (!(file.type || '').startsWith('image/')) {
      window.showToast?.('Выберите файл изображения (JPG, PNG, WebP).', 'warning');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      document.getElementById('teacherImagePreviewImg').src = event.target.result;
      document.getElementById('teacherImageFileName').textContent = `${file.name} (${Math.round(file.size / 1024)} КБ)`;
      document.getElementById('teacherUploadPlaceholder').style.display = 'none';
      document.getElementById('teacherPreviewContainer').style.display = 'flex';
    };
    reader.readAsDataURL(file);
  };
  window.previewTeacherImage = showPreview;
  input.addEventListener('click', event => event.stopPropagation());
  input.addEventListener('change', () => showPreview(input.files?.[0]));
  dropArea.addEventListener('click', event => {
    if (!event.target.closest('button')) input.click();
  });
  document.getElementById('removeTeacherPhotoBtn')?.addEventListener('click', event => {
    event.preventDefault();
    event.stopPropagation();
    window.resetTeacherPhotoPreview();
  });
  dropArea.addEventListener('dragover', event => event.preventDefault());
  dropArea.addEventListener('drop', event => {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (!file) return;
    try {
      const transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
    } catch (_) {}
    showPreview(file);
  });
}

function initializeTeacherDossierImagePreview() {
  const input = document.getElementById('teacherDossierImageUpload');
  const photo = document.getElementById('teacherDossierPhoto');
  if (!input || !photo || input.dataset.previewInitialized === 'true') return;
  input.dataset.previewInitialized = 'true';
  input.addEventListener('change', () => {
    const file = input.files?.[0];
    if (!file || !(file.type || '').startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = event => { photo.src = event.target.result; };
    reader.readAsDataURL(file);
  });
}

document.addEventListener('DOMContentLoaded', initializeTeacherImagePreview);
document.addEventListener('DOMContentLoaded', initializeTeacherDossierImagePreview);

// --- УЧИТЕЛЯ ---
window.loadAdminTeachers = async function() {
  const container = document.querySelector('#tab-teachers .directory-list');
  if (!container) return;
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Загрузка преподавателей...</div>';
  
  try {
    // Backend API Inventory says GET /api/accounts/users is available
    const res = await apiFetch('/accounts/users?role=teacher');
    const payload = res.ok ? await res.json() : { data: [] };
    const teachers = payload.data || [];
    
    if (!teachers.length) {
      container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Преподавателей пока нет.</div>';
      return;
    }
    
    container.innerHTML = teachers.map(t => `
      <div class="directory-row" onclick="openTeacherDossier(${t.id})">
        <div class="dir-identity">
          <div class="dir-avatar">
            <img src="${t.avatar_url || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(t.full_name || t.email)}" alt="" onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(t.full_name || t.email)}'">
          </div>
          <div class="dir-info">
            <span class="dir-name">${t.full_name || t.email}</span>
            <span class="dir-meta">${t.email || ''}</span>
          </div>
        </div>
        <div class="dir-actions">
          <button class="btn-icon" title="Редактировать профиль" onclick="event.stopPropagation(); openTeacherDossier(${t.id})"><iconify-icon icon="solar:pen-bold-duotone"></iconify-icon></button>
          <button class="btn-icon-danger" title="Удалить преподавателя" onclick="event.stopPropagation(); deleteTeacherAdmin(${t.id})"><iconify-icon icon="solar:trash-bin-trash-bold"></iconify-icon></button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div style="padding: 32px; color: red;">Ошибка: ${err.message}</div>`;
  }
};

window.deleteTeacherAdmin = async function(teacherId) {
  const confirmed = window.showConfirm ? await window.showConfirm({
    title: 'Удалить преподавателя?',
    message: 'Будут удалены профиль, назначения в группах и расписание преподавателя.',
    type: 'danger',
    confirmText: 'Да, удалить',
    cancelText: 'Отмена',
  }) : confirm('Удалить преподавателя?');
  if (!confirmed) return;
  try {
    const response = await apiFetch(`/accounts/teachers/${teacherId}`, { method: 'DELETE' });
    if (!response.ok && response.status !== 204) throw new Error('Не удалось удалить преподавателя');
    window.showToast?.('Преподаватель удален', 'success');
    await loadAdminTeachers();
  } catch (error) {
    window.showToast?.(error.message, 'error');
  }
};

// --- ПРОГРАММЫ ---
window.loadAdminPrograms = async function() {
  const container = document.querySelector('#tab-programs .programs-list');
  if (!container) return;
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Загрузка программ...</div>';
  
  try {
    const res = await apiFetch('/education/programs');
    const payload = await res.json();
    const programs = payload.data || [];

    container.innerHTML = '';
    if (!programs.length) {
      container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Программ пока нет.</div>';
      return;
    }

    programs.forEach(program => {
      const card = document.createElement('div');
      card.className = 'program-card';
      card.innerHTML = `
        <div class="program-header">
          <div class="program-title-wrap">
            <div class="program-icon"><iconify-icon icon="solar:music-note-bold-duotone"></iconify-icon></div>
            <div>
              <div class="program-name-container">
                <div class="program-name"></div>
                <button class="edit-program-btn" type="button" title="Изменить программу">
                  <iconify-icon icon="solar:pen-bold-duotone"></iconify-icon>
                </button>
              </div>
              <div class="program-level"></div>
              <div class="program-description"></div>
            </div>
          </div>
          <div class="program-meta">
            <span class="groups-count">Программа</span>
            <iconify-icon class="chevron" icon="solar:alt-arrow-down-bold"></iconify-icon>
          </div>
        </div>
        <div class="program-body">
          <div class="groups-list">
            <div class="group-row"><div class="group-info"><div class="group-name">Загрузка...</div></div></div>
          </div>
        </div>`;
      card.querySelector('.program-header').onclick = async () => {
        const isActive = card.classList.toggle('active');
        if (!isActive || card.dataset.loaded === 'true') return;
        try {
          const [structureResponse, groupsResponse] = await Promise.all([
            requestJson(`/education/programs/${program.id}/structure`),
            requestJson('/education/groups'),
          ]);
          card.dataset.loaded = 'true';
          const structure = structureResponse?.data;
          const planRow = card.querySelector('.group-row');
          if (structure) {
            planRow.querySelector('.group-name').textContent = `${structure.blocks?.length || 0} блоков учебного плана`;
          }
          renderProgramGroups(card, program, groupsResponse.data || []);
        } catch (error) {
          card.querySelector('.groups-list').innerHTML = `<div class="group-row"><div class="group-info"><div class="group-name">Ошибка загрузки</div><div class="group-students">${error.message}</div></div></div>`;
        }
      };
      card.querySelector('.edit-program-btn').onclick = (event) => {
        event.stopPropagation();
        openEditProgramModal(program.id);
      };
      card.querySelector('.program-name').textContent = program.title || 'Без названия';
      card.querySelector('.program-level').textContent = program.status === 'draft' ? 'Черновик' : program.status || '';
      card.querySelector('.program-description').textContent = program.description || 'Описание отсутствует';
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<div style="padding: 32px; color: var(--pal-accent-red);">Ошибка: ${err.message}</div>`;
  }
};

// --- КОНСУЛЬТАЦИИ ---
let consultationDaysByDate = new Map();
let activeConsultationDate = null;
let currentConsultationWeekOffset = 0;
let weekControlsInitialized = false;

function getLocalDateKey(dateInput) {
  if (!dateInput) return '';
  if (typeof dateInput === 'string') {
    const match = dateInput.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (match && !dateInput.endsWith('Z') && !dateInput.includes('+')) {
      return `${match[1]}-${match[2]}-${match[3]}`;
    }
    const d = new Date(dateInput);
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }
    return dateInput.slice(0, 10);
  }
  const y = dateInput.getFullYear();
  const m = String(dateInput.getMonth() + 1).padStart(2, '0');
  const day = String(dateInput.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function consultationWeekStart() {
  const date = new Date();
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff + (currentConsultationWeekOffset * 7));
  date.setHours(0, 0, 0, 0);
  return date;
}

function consultationDateKey(date) {
  return getLocalDateKey(date);
}

window.changeConsultationWeek = function(offsetDelta) {
  currentConsultationWeekOffset += offsetDelta;
  loadAdminConsultations();
};

function initConsultationWeekControls() {
  if (weekControlsInitialized) return;
  const prevBtn = document.getElementById('adminConsultationPreviousWeek');
  const nextBtn = document.getElementById('adminConsultationNextWeek');
  if (prevBtn && nextBtn) {
    prevBtn.onclick = () => window.changeConsultationWeek(-1);
    nextBtn.onclick = () => window.changeConsultationWeek(1);
    weekControlsInitialized = true;
  }
}

let allConsultationSlots = [];
let activeConsultationSlot = null;
let activeSlotParticipants = [];
let consultationPickerMode = 'create'; // 'create' | 'addToSlot'

window.loadAdminConsultations = async function() {
  const header = document.getElementById('consultationsCalendarHeader');
  const body = document.getElementById('consultationsCalendarBody');
  if (!header || !body) return;

  initConsultationWeekControls();

  try {
    const [daysResponse, slotsResponse, studentsResponse] = await Promise.all([
      requestJson('/consultations/admin/days').catch(() => ({ items: [] })),
      requestJson('/consultations/admin/slots').catch(() => ({ items: [] })),
      allConsultationStudentsList.length ? Promise.resolve({ data: allConsultationStudentsList }) : requestJson('/education/students').catch(() => ({ data: [] }))
    ]);

    if (studentsResponse?.data?.length) {
      allConsultationStudentsList = studentsResponse.data;
    }

    const slots = slotsResponse.items || [];

    // Подгружаем участников для каждого слота, чтобы сразу вывести на карточках в расписании
    const participantsResults = await Promise.all(slots.map(async slot => {
      try {
        const res = await requestJson(`/consultations/admin/slots/${slot.id}/participants`);
        return { slotId: slot.id, participants: res.items || [] };
      } catch {
        return { slotId: slot.id, participants: [] };
      }
    }));

    const slotParticipantsMap = new Map(participantsResults.map(r => [r.slotId, r.participants.filter(participant => participant.booking_status === 'CONFIRMED')]));
    const occupiedSlots = slots.filter(slot => (slotParticipantsMap.get(slot.id) || []).length > 0);
    allConsultationSlots = occupiedSlots;

    renderConsultationCalendar(daysResponse.items || [], occupiedSlots, slotParticipantsMap);
  } catch (error) {
    body.innerHTML = `<div style="grid-column: 1 / -1; padding: 32px; color: var(--pal-accent-red);">Не удалось загрузить консультации: ${error.message}</div>`;
  }
};

function renderConsultationCalendar(days, slots, slotParticipantsMap = new Map()) {
  allConsultationSlots = slots || [];
  const header = document.getElementById('consultationsCalendarHeader');
  const body = document.getElementById('consultationsCalendarBody');
  const weekStart = consultationWeekStart();
  const weekDates = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(weekStart);
    date.setDate(weekStart.getDate() + index);
    return date;
  });

  const dayByDate = new Map((days || []).map(day => [getLocalDateKey(day.date), day]));
  consultationDaysByDate = dayByDate;

  const slotsByDay = new Map();
  (slots || []).forEach(slot => {
    const dateKey = getLocalDateKey(slot.start_at);
    if (!slotsByDay.has(dateKey)) slotsByDay.set(dateKey, []);
    slotsByDay.get(dateKey).push(slot);
  });

  // Обновление отображения диапазона недели
  const weekLabel = document.getElementById('adminConsultationWeekLabel');
  if (weekLabel) {
    const startDay = weekDates[0];
    const endDay = weekDates[6];
    const startStr = startDay.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    const endStr = endDay.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
    weekLabel.textContent = `${startStr} — ${endStr}`;
  }

  const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  const todayKey = getLocalDateKey(new Date());

  header.innerHTML = '<div class="time-spacer" style="border-right: 1px solid rgba(255,255,255,0.03);"></div>' + weekDates.map((date, index) => {
    const key = getLocalDateKey(date);
    const day = dayByDate.get(key);
    const isToday = key === todayKey;
    return `<div class="calendar-header-cell ${day?.status === 'CLOSED' ? 'blocked' : ''} ${isToday ? 'active-day' : ''}" data-consultation-date="${key}" onclick="openDayConfigModal('${key}')">
      <div class="day-name">${dayNames[index]}</div><div class="day-date">${String(date.getDate()).padStart(2, '0')}</div>
    </div>`;
  }).join('');

  const studentMap = new Map((allConsultationStudentsList || []).map(s => [s.id, s]));

  body.innerHTML = '<div class="time-scale">' + Array.from({ length: 12 }, (_, index) => `<div class="time-label"><span>${String(index + 9).padStart(2, '0')}:00</span></div>`).join('') + '</div>' + weekDates.map((date) => {
    const key = getLocalDateKey(date);
    const day = dayByDate.get(key);
    const closed = day?.status === 'CLOSED';
    const daySlots = slotsByDay.get(key) || [];
    const workTime = day?.available_from && day?.available_to ? `<div class="work-time-bg" style="top:${calendarTimeOffset(day.available_from)}px;height:${calendarDuration(day.available_from, day.available_to)}px"></div>` : '';
    
    const cards = daySlots.map(slot => {
      const start = new Date(slot.start_at);
      const end = new Date(slot.end_at);
      const top = Math.max(0, (start.getHours() + start.getMinutes() / 60 - 9) * 60);
      const height = Math.max(48, ((end.getTime() - start.getTime()) / 60000) || 60);
      const timeStr = `${start.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`;
      
      const participants = slotParticipantsMap.get(slot.id) || [];
      const namesHtml = participants.map(p => {
          const student = studentMap.get(p.student_id);
          const name = student?.full_name || (student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : '') || student?.email || `Ученик #${p.student_id}`;
          const isPresent = p.attendance_status === 'PRESENT';
          const isPaid = p.payment_status === 'PAID';
          
          let badges = '';
          if (isPresent) badges += '<iconify-icon icon="solar:check-circle-bold" style="color:var(--pal-light-green); font-size: 0.85rem;" title="Присутствовал"></iconify-icon>';
          if (isPaid) badges += '<iconify-icon icon="solar:wallet-money-bold" style="color:#F2C94C; font-size: 0.85rem;" title="Оплачено"></iconify-icon>';
          
          return `<div style="display:flex; align-items:center; justify-content:space-between; gap:4px; font-size:0.76rem; color:var(--text-main); font-weight:600; line-height:1.2;">
            <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${name}</span>
            <div style="display:flex; gap:2px; flex-shrink:0;">${badges}</div>
          </div>`;
        }).join('');

      return `
        <div class="consultation-card ${slot.access_mode === 'INVITED' ? 'admin-scheduled' : ''}" 
             style="top:${top}px;height:${height}px" 
             onclick="event.stopPropagation(); openConsultationParticipants(${slot.id})" 
             title="Нажмите для просмотра учеников и отметки статусов">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px;">
            <span class="status-label" style="font-size: 0.68rem; font-weight: 700; color: #82B1FF;">${timeStr}</span>
            <span style="font-size: 0.65rem; padding: 1px 5px; border-radius: 8px; background: rgba(255,255,255,0.08); font-weight: 700;">
              ${participants.length}/4
            </span>
          </div>
          ${namesHtml}
        </div>
      `;
    }).join('');

    return `<div class="day-grid-col ${closed ? 'blocked' : ''}" data-consultation-date="${key}" onclick="openDayConfigModal('${key}')">${workTime}${cards}</div>`;
  }).join('');
}

window.openDayConfigModal = function(dateKey) {
  activeConsultationDate = dateKey;
  const day = consultationDaysByDate.get(dateKey);
  const date = new Date(`${dateKey}T12:00:00`);
  document.getElementById('configDayTitle').textContent = date.toLocaleDateString('ru-RU', { weekday: 'long' });
  document.getElementById('configDayDate').textContent = date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' });
  document.getElementById('dayStatusToggle').checked = day?.status !== 'CLOSED';
  document.getElementById('dayAvailableFrom').value = day?.available_from?.slice(0, 5) || '09:00';
  document.getElementById('dayAvailableTo').value = day?.available_to?.slice(0, 5) || '18:00';
  openModal('dayConfigModal');
};

window.saveDayConfig = async function() {
  const availableFrom = document.getElementById('dayAvailableFrom').value;
  const availableTo = document.getElementById('dayAvailableTo').value;
  const status = document.getElementById('dayStatusToggle').checked ? 'OPEN' : 'CLOSED';
  if (availableFrom && availableTo && availableFrom >= availableTo) {
    showToast('Время окончания должно быть позже времени начала.', 'warning');
    return;
  }
  try {
    const payload = { status, available_from: availableFrom || null, available_to: availableTo || null };
    const day = consultationDaysByDate.get(activeConsultationDate);
    if (day) {
      await requestJson(`/consultations/admin/days/${day.id}/window`, { method: 'PATCH', body: JSON.stringify(payload) });
    } else {
      await requestJson('/consultations/admin/days', { method: 'POST', body: JSON.stringify({ date: activeConsultationDate, ...payload }) });
    }
    closeModal('dayConfigModal');
    await loadAdminConsultations();
    showToast('Время записи сохранено', 'success');
  } catch (error) {
    showToast(`Не удалось сохранить время записи: ${error.message}`, 'error');
  }
};

function calendarTimeOffset(value) {
  const [hours, minutes] = value.slice(0, 5).split(':').map(Number);
  return Math.max(0, (hours + minutes / 60 - 9) * 60);
}

function calendarDuration(from, to) {
  return Math.max(0, calendarTimeOffset(to) - calendarTimeOffset(from));
}

let defaultConsultationTeacherId = null;
let allConsultationStudentsList = [];
let selectedConsultationStudentIds = new Set();
let currentConsultationDuration = 60;

window.ensureConsultationTeacher = async function() {
  if (defaultConsultationTeacherId) return defaultConsultationTeacherId;
  try {
    const response = await requestJson('/accounts/users?role=teacher');
    const teachers = response.data || [];
    if (teachers.length) {
      defaultConsultationTeacherId = teachers[0].id;
    } else {
      defaultConsultationTeacherId = 1;
    }
  } catch {
    defaultConsultationTeacherId = 1;
  }
  return defaultConsultationTeacherId;
};

// Открытие окна управления консультацией и списком учеников
window.openConsultationParticipants = async function(slotId) {
  activeConsultationSlot = (allConsultationSlots || []).find(s => s.id === slotId) || { id: slotId };
  activeSlotParticipants = [];
  
  const dateEl = document.getElementById('manageConsultationDateTime');
  const subEl = document.getElementById('manageConsultationSubInfo');
  const listEl = document.getElementById('manageConsultationStudentsList');
  const totalBadge = document.getElementById('manageConsultationTotalBadge');
  const attendedBadge = document.getElementById('manageConsultationAttendedBadge');
  const paidBadge = document.getElementById('manageConsultationPaidBadge');
  
  if (activeConsultationSlot.start_at && activeConsultationSlot.end_at) {
    const startDate = new Date(activeConsultationSlot.start_at);
    const endDate = new Date(activeConsultationSlot.end_at);
    const dateFormatted = startDate.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' });
    const startTime = startDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    const endTime = endDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    if (dateEl) dateEl.textContent = `${dateFormatted.charAt(0).toUpperCase() + dateFormatted.slice(1)} • ${startTime} – ${endTime}`;
  } else {
    if (dateEl) dateEl.textContent = `Консультация #${slotId}`;
  }
  if (subEl) subEl.textContent = 'Ведущий: Администратор Studio Alanko';

  if (totalBadge) totalBadge.textContent = '0 / 4 мест';
  if (attendedBadge) attendedBadge.textContent = 'Пришли: 0';
  if (paidBadge) paidBadge.textContent = 'Оплачено: 0';

  if (listEl) {
    listEl.innerHTML = `
      <div style="padding: 30px; text-align: center; color: var(--text-muted);">
        <iconify-icon icon="solar:spinner-line-duotone" style="font-size: 2rem; animation: spin 1s linear infinite;"></iconify-icon>
        <div style="margin-top: 8px;">Загрузка списка учеников...</div>
      </div>
    `;
  }

  openModal('manageConsultationModal');

  try {
    const [participantsRes, studentsRes] = await Promise.all([
      requestJson(`/consultations/admin/slots/${slotId}/participants`),
      allConsultationStudentsList.length ? Promise.resolve({ data: allConsultationStudentsList }) : requestJson('/education/students').catch(() => ({ data: [] }))
    ]);

    if (studentsRes?.data?.length) {
      allConsultationStudentsList = studentsRes.data;
    }

    activeSlotParticipants = participantsRes?.items || [];
    renderActiveSlotParticipants();
  } catch (error) {
    if (listEl) {
      listEl.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--pal-accent-red);">
          Не удалось загрузить данные: ${error.message}
        </div>
      `;
    }
  }
};

window.renderActiveSlotParticipants = function() {
  const listEl = document.getElementById('manageConsultationStudentsList');
  const totalBadge = document.getElementById('manageConsultationTotalBadge');
  const attendedBadge = document.getElementById('manageConsultationAttendedBadge');
  const paidBadge = document.getElementById('manageConsultationPaidBadge');
  const addBtn = document.getElementById('manageConsultationAddStudentBtn');

  const studentMap = new Map((allConsultationStudentsList || []).map(s => [s.id, s]));
  const count = activeSlotParticipants.length;
  const attendedCount = activeSlotParticipants.filter(p => p.attendance_status === 'PRESENT').length;
  const paidCount = activeSlotParticipants.filter(p => p.payment_status === 'PAID').length;

  if (totalBadge) totalBadge.textContent = `${count} / 4 мест`;
  if (attendedBadge) attendedBadge.textContent = `Пришли: ${attendedCount}`;
  if (paidBadge) paidBadge.textContent = `Оплачено: ${paidCount}`;

  if (addBtn) {
    addBtn.style.display = count >= 4 ? 'none' : 'inline-flex';
  }

  if (!listEl) return;

  if (!count) {
    listEl.innerHTML = `
      <div style="padding: 36px 20px; text-align: center; background: rgba(255,255,255,0.02); border: 1px dashed var(--card-border); border-radius: var(--radius-lg); color: var(--text-muted);">
        <iconify-icon icon="solar:users-group-rounded-bold-duotone" style="font-size: 2.5rem; opacity: 0.4; margin-bottom: 8px;"></iconify-icon>
        <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-main);">Пока нет зарегистрированных учеников</div>
        <div style="font-size: 0.8rem; margin-top: 4px; margin-bottom: 16px;">Вы можете добавить учеников из базы или дождаться самостоятельной записи.</div>
        <button type="button" class="btn btn-secondary btn-sm" onclick="openAddStudentToActiveConsultation()">
          <iconify-icon icon="solar:user-plus-bold"></iconify-icon> Добавить первого ученика
        </button>
      </div>
    `;
    return;
  }

  listEl.innerHTML = activeSlotParticipants.map(participant => {
    const student = studentMap.get(participant.student_id) || { id: participant.student_id };
    const name = student.full_name || `${student.first_name || ''} ${student.last_name || ''}`.trim() || student.email || `Ученик #${participant.student_id}`;
    const initials = (name.split(' ').map(n => n[0]).join('').slice(0, 2) || 'У').toUpperCase();
    const meta = student.phone || (student.age ? `Возраст: ${student.age} лет` : (student.email || ''));
    const avatarHtml = student.image_url 
      ? `<img src="${student.image_url}" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"><span style="display:none;">${initials}</span>`
      : initials;

    const isPresent = participant.attendance_status === 'PRESENT';
    const isPaid = participant.payment_status === 'PAID';

    return `
      <div class="participant-manage-card" id="participantCard_${participant.id}">
        <div class="participant-info-col">
          <div class="participant-avatar-box">
            ${avatarHtml}
          </div>
          <div style="min-width: 0;">
            <div class="participant-name-text" title="${name}">${name}</div>
            <div class="participant-meta-text">${meta || 'Зарегистрирован на консультацию'}</div>
          </div>
        </div>

        <div class="participant-actions-col">
          <!-- Группа переключения присутствия: Пришел / Не пришел -->
          <div class="status-segment-group" title="Статус присутствия ученика">
            <button type="button" 
              class="status-segment-btn ${isPresent ? 'active-present' : ''}" 
              title="Отметить: Присутствует на консультации"
              onclick="setParticipantAttendance(${participant.id}, 'PRESENT')">
              <iconify-icon icon="solar:check-circle-bold"></iconify-icon>
              <span>Пришел</span>
            </button>
            <button type="button" 
              class="status-segment-btn ${!isPresent ? 'active-absent' : ''}" 
              title="Отметить: Отсутствует"
              onclick="setParticipantAttendance(${participant.id}, 'ABSENT')">
              <iconify-icon icon="solar:close-circle-bold"></iconify-icon>
              <span>Не пришел</span>
            </button>
          </div>

          <!-- Группа переключения оплаты: Оплачено / Не оплачено -->
          <div class="status-segment-group" title="Статус оплаты консультации">
            <button type="button" 
              class="status-segment-btn ${isPaid ? 'active-paid' : ''}" 
              title="Отметить: Консультация оплачена"
              onclick="setParticipantPayment(${participant.id}, 'PAID')">
              <iconify-icon icon="solar:wallet-money-bold"></iconify-icon>
              <span>Оплачено</span>
            </button>
            <button type="button" 
              class="status-segment-btn ${!isPaid ? 'active-unpaid' : ''}" 
              title="Отметить: Консультация не оплачена"
              onclick="setParticipantPayment(${participant.id}, 'UNPAID')">
              <iconify-icon icon="solar:card-2-bold"></iconify-icon>
              <span>Не оплачено</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
};

// Установка конкретного статуса присутствия ученика ('PRESENT' | 'ABSENT')
window.setParticipantAttendance = async function(participantId, targetStatus) {
  const participant = activeSlotParticipants.find(p => p.id === participantId);
  if (!participant) return;
  
  const previousStatus = participant.attendance_status;
  if (previousStatus === targetStatus) return; // Уже в этом статусе

  participant.attendance_status = targetStatus;
  renderActiveSlotParticipants();

  try {
    await requestJson(`/consultations/admin/participants/${participantId}/attendance`, {
      method: 'PATCH',
      body: JSON.stringify({ status: targetStatus }),
    });
    showToast(targetStatus === 'PRESENT' ? 'Посещение: ученик отмечен как «Пришел»' : 'Посещение: отмечен статус «Не пришел»', 'info');
    loadAdminConsultations();
  } catch (error) {
    participant.attendance_status = previousStatus;
    renderActiveSlotParticipants();
    showToast(`Не удалось обновить статус присутствия: ${error.message}`, 'error');
  }
};

// Установка конкретного статуса оплаты ученика ('PAID' | 'UNPAID')
window.setParticipantPayment = async function(participantId, targetStatus) {
  const participant = activeSlotParticipants.find(p => p.id === participantId);
  if (!participant) return;
  
  const previousStatus = participant.payment_status;
  if (previousStatus === targetStatus) return; // Уже в этом статусе

  participant.payment_status = targetStatus;
  renderActiveSlotParticipants();

  try {
    await requestJson(`/consultations/admin/participants/${participantId}/payment`, {
      method: 'PATCH',
      body: JSON.stringify({ status: targetStatus }),
    });
    showToast(targetStatus === 'PAID' ? 'Оплата: отмечено как «Оплачено»' : 'Оплата: отмечено как «Не оплачено»', 'info');
    loadAdminConsultations();
  } catch (error) {
    participant.payment_status = previousStatus;
    renderActiveSlotParticipants();
    showToast(`Не удалось обновить статус оплаты: ${error.message}`, 'error');
  }
};

// Переключение статуса присутствия ученика (для совместимости)
window.toggleParticipantAttendance = async function(participantId, currentStatus) {
  const nextStatus = currentStatus === 'PRESENT' ? 'ABSENT' : 'PRESENT';
  return window.setParticipantAttendance(participantId, nextStatus);
};

// Переключение статуса оплаты ученика (для совместимости)
window.toggleParticipantPayment = async function(participantId, currentStatus) {
  const nextStatus = currentStatus === 'PAID' ? 'UNPAID' : 'PAID';
  return window.setParticipantPayment(participantId, nextStatus);
};

// Добавление ученика в уже созданную консультацию
window.openAddStudentToActiveConsultation = async function() {
  if (!activeConsultationSlot) return;
  consultationPickerMode = 'addToSlot';
  
  if (!allConsultationStudentsList.length) {
    try {
      const response = await requestJson('/education/students');
      allConsultationStudentsList = response.data || [];
    } catch (error) {
      showToast(`Не удалось загрузить список учеников: ${error.message}`, 'error');
    }
  }

  selectedConsultationStudentIds.clear();
  const searchInput = document.getElementById('consultationStudentSearchInput');
  if (searchInput) searchInput.value = '';

  renderConsultationStudentsPicker();
  updateConsultationPickerCounters();
  openModal('selectConsultationStudentsModal');
};

window.openConsultationModal = async function(presetDate) {
  consultationPickerMode = 'create';
  const dateInput = document.getElementById('consultationDate');
  const startInput = document.getElementById('consultationStart');
  const endInput = document.getElementById('consultationEnd');
  
  if (dateInput) {
    dateInput.value = presetDate || consultationDateKey(new Date());
  }
  if (startInput) startInput.value = '18:00';
  if (endInput) endInput.value = '19:00';
  
  selectedConsultationStudentIds.clear();
  renderConsultationSlots();
  ensureConsultationTeacher();
  
  openModal('createConsultationModal');
};

window.setConsultationDuration = function(minutes, btnEl) {
  currentConsultationDuration = minutes;
  if (btnEl) {
    const parent = btnEl.closest('.time-presets-row');
    if (parent) {
      parent.querySelectorAll('.time-preset-btn').forEach(btn => btn.classList.remove('active'));
      btnEl.classList.add('active');
    }
  }
  const startInput = document.getElementById('consultationStart');
  const endInput = document.getElementById('consultationEnd');
  if (!startInput || !endInput || !startInput.value) return;

  const [hours, mins] = startInput.value.split(':').map(Number);
  const totalMinutes = hours * 60 + mins + minutes;
  const newHours = Math.floor(totalMinutes / 60) % 24;
  const newMins = totalMinutes % 60;
  endInput.value = `${String(newHours).padStart(2, '0')}:${String(newMins).padStart(2, '0')}`;
};

window.onConsultationStartTimeChange = function() {
  setConsultationDuration(currentConsultationDuration || 60);
};

window.renderConsultationSlots = function() {
  const container = document.getElementById('consultationSlotsContainer');
  const counterNumber = document.getElementById('consultationSelectedCountNumber');
  if (!container) return;

  const studentMap = new Map(allConsultationStudentsList.map(s => [s.id, s]));
  const selectedStudents = Array.from(selectedConsultationStudentIds).map(id => studentMap.get(id) || { id, full_name: `Ученик #${id}` });

  if (counterNumber) {
    counterNumber.textContent = selectedStudents.length;
  }

  const MAX_SLOTS = 4;
  let html = '';

  for (let i = 0; i < MAX_SLOTS; i++) {
    const student = selectedStudents[i];
    if (student) {
      const name = student.full_name || `${student.first_name || ''} ${student.last_name || ''}`.trim() || student.email || `Ученик #${student.id}`;
      const initials = (name.split(' ').map(n => n[0]).join('').slice(0, 2) || 'У').toUpperCase();
      const meta = student.phone || student.email || (student.age ? `Возраст: ${student.age} лет` : 'Приглашён на консультацию');
      const avatarHtml = student.image_url 
        ? `<img src="${student.image_url}" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"><span style="display:none;">${initials}</span>`
        : initials;

      html += `
        <div class="consultation-slot-card filled" id="consultationSlot_${i}">
          <div class="slot-student-info">
            <div class="slot-avatar">${avatarHtml}</div>
            <div class="slot-details">
              <div class="slot-name">${name}</div>
              <div class="slot-meta">${meta}</div>
            </div>
          </div>
          <button type="button" class="slot-remove-btn" title="Удалить из списка" onclick="removeConsultationStudent(${student.id})">
            <iconify-icon icon="solar:close-circle-bold"></iconify-icon>
          </button>
        </div>
      `;
    } else {
      html += `
        <div class="consultation-slot-card empty" id="consultationSlot_${i}" onclick="openSelectConsultationStudentsModal()">
          <div class="empty-slot-content">
            <div class="empty-slot-icon">
              <iconify-icon icon="solar:add-circle-bold"></iconify-icon>
            </div>
            <span>Свободное место №${i + 1} (нажмите, чтобы выбрать ученика)</span>
          </div>
        </div>
      `;
    }
  }

  container.innerHTML = html;
};

window.removeConsultationStudent = function(studentId) {
  selectedConsultationStudentIds.delete(studentId);
  renderConsultationSlots();
};

window.openSelectConsultationStudentsModal = async function() {
  consultationPickerMode = 'create';
  if (!allConsultationStudentsList.length) {
    try {
      const response = await requestJson('/education/students');
      allConsultationStudentsList = response.data || [];
    } catch (error) {
      showToast(`Не удалось загрузить список учеников: ${error.message}`, 'error');
    }
  }

  const searchInput = document.getElementById('consultationStudentSearchInput');
  if (searchInput) searchInput.value = '';
  
  renderConsultationStudentsPicker();
  updateConsultationPickerCounters();
  openModal('selectConsultationStudentsModal');
};

window.renderConsultationStudentsPicker = function(searchQuery = '') {
  const grid = document.getElementById('consultationStudentsPickerGrid');
  if (!grid) return;

  const existingParticipantIds = consultationPickerMode === 'addToSlot' 
    ? new Set(activeSlotParticipants.map(p => p.student_id))
    : new Set();

  const query = searchQuery.trim().toLowerCase();
  const filtered = allConsultationStudentsList.filter(student => {
    // If adding to slot, don't show students already enrolled
    if (existingParticipantIds.has(student.id)) return false;

    if (!query) return true;
    const name = (student.full_name || `${student.first_name || ''} ${student.last_name || ''}`.trim() || '').toLowerCase();
    const phone = (student.phone || '').toLowerCase();
    const email = (student.email || '').toLowerCase();
    return name.includes(query) || phone.includes(query) || email.includes(query);
  });

  if (!filtered.length) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: var(--text-muted);">
        <iconify-icon icon="solar:users-group-rounded-bold-duotone" style="font-size: 2.5rem; color: var(--card-border); margin-bottom: 8px;"></iconify-icon>
        <div>${query ? 'По запросу «' + searchQuery + '» учеников не найдено' : 'Список учеников пуст или все ученики уже добавлены'}</div>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(student => {
    const isSelected = selectedConsultationStudentIds.has(student.id);
    const name = student.full_name || `${student.first_name || ''} ${student.last_name || ''}`.trim() || student.email || `Ученик #${student.id}`;
    const initials = (name.split(' ').map(n => n[0]).join('').slice(0, 2) || 'У').toUpperCase();
    const meta = student.phone || (student.age ? `Возраст: ${student.age} лет` : (student.email || ''));
    const avatarHtml = student.image_url 
      ? `<img src="${student.image_url}" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"><span style="display:none;">${initials}</span>`
      : initials;

    return `
      <div class="student-select-card ${isSelected ? 'selected' : ''}" onclick="toggleConsultationStudentSelection(${student.id}, this)">
        <div class="student-photo" style="background: rgba(255,255,255,0.05); color: var(--pal-light-green); font-weight: bold; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0;">
          ${avatarHtml}
        </div>
        <div class="student-card-info">
          <div class="student-card-name" title="${name}">${name}</div>
          <div class="student-card-meta">
            ${meta ? `<span>${meta}</span>` : ''}
          </div>
        </div>
        <div class="checkbox-circle">
          <iconify-icon icon="solar:check-read-bold"></iconify-icon>
        </div>
      </div>
    `;
  }).join('');
};

window.filterConsultationStudentsPicker = function(value) {
  renderConsultationStudentsPicker(value);
};

window.toggleConsultationStudentSelection = function(studentId, cardEl) {
  const maxAllowed = consultationPickerMode === 'addToSlot' 
    ? (4 - activeSlotParticipants.length) 
    : 4;

  if (selectedConsultationStudentIds.has(studentId)) {
    selectedConsultationStudentIds.delete(studentId);
    if (cardEl) cardEl.classList.remove('selected');
  } else {
    if (selectedConsultationStudentIds.size >= maxAllowed) {
      showToast(`Можно выбрать максимум ${maxAllowed} ученик(а)`, 'warning');
      return;
    }
    selectedConsultationStudentIds.add(studentId);
    if (cardEl) cardEl.classList.add('selected');
  }
  updateConsultationPickerCounters();
};

window.updateConsultationPickerCounters = function() {
  const count = selectedConsultationStudentIds.size;
  const countEl = document.getElementById('consultationPickerCount');
  const applyCountEl = document.getElementById('consultationPickerApplyCount');
  if (countEl) countEl.textContent = count;
  if (applyCountEl) applyCountEl.textContent = count;
};

window.clearConsultationStudentSelection = function() {
  selectedConsultationStudentIds.clear();
  const searchInput = document.getElementById('consultationStudentSearchInput');
  renderConsultationStudentsPicker(searchInput?.value || '');
  updateConsultationPickerCounters();
};

window.applyConsultationStudentSelection = async function() {
  closeModal('selectConsultationStudentsModal');

  if (consultationPickerMode === 'addToSlot') {
    const studentIds = Array.from(selectedConsultationStudentIds);
    if (!studentIds.length) return;
    if (!activeConsultationSlot) return;

    try {
      await requestJson(`/consultations/admin/slots/${activeConsultationSlot.id}/invitations`, {
        method: 'POST',
        body: JSON.stringify({ student_ids: studentIds }),
      });

      const response = await requestJson(`/consultations/admin/slots/${activeConsultationSlot.id}/participants`);
      activeSlotParticipants = response.items || [];
      renderActiveSlotParticipants();
      showToast('Ученики успешно добавлены на консультацию', 'success');
      loadAdminConsultations();
    } catch (error) {
      showToast(`Не удалось добавить учеников: ${error.message}`, 'error');
    }
  } else {
    renderConsultationSlots();
  }
};

window.saveConsultation = async function() {
  const dateInput = document.getElementById('consultationDate');
  const startInput = document.getElementById('consultationStart');
  const endInput = document.getElementById('consultationEnd');
  
  const date = dateInput ? dateInput.value : '';
  const start = startInput ? startInput.value : '';
  const end = endInput ? endInput.value : '';
  const teacherId = await ensureConsultationTeacher();
  const capacity = 4;
  const studentIds = Array.from(selectedConsultationStudentIds);

  if (!date || !start || !end) {
    showToast('Пожалуйста, укажите дату и время консультации.', 'warning');
    return;
  }
  if (start >= end) {
    showToast('Время окончания должно быть позже времени начала.', 'warning');
    return;
  }

  try {
    const daysResponse = await requestJson('/consultations/admin/days');
    let day = (daysResponse.items || []).find(item => item.date === date);
    if (!day) {
      day = await requestJson('/consultations/admin/days', { 
        method: 'POST', 
        body: JSON.stringify({ date, status: 'OPEN' }) 
      });
    }
    
    const slot = await requestJson('/consultations/admin/slots', {
      method: 'POST',
      body: JSON.stringify({ 
        day_id: day.id, 
        teacher_id: teacherId, 
        start_at: `${date}T${start}:00`, 
        end_at: `${date}T${end}:00`, 
        capacity, 
        price: 0, 
        currency: 'RUB', 
        access_mode: studentIds.length ? 'INVITED' : 'PUBLIC' 
      }),
    });

    if (studentIds.length) {
      await requestJson(`/consultations/admin/slots/${slot.id}/invitations`, {
        method: 'POST',
        body: JSON.stringify({ student_ids: studentIds }),
      });
    }

    closeModal('createConsultationModal');
    await loadAdminConsultations();
    showToast('Консультация успешно создана', 'success');
  } catch (error) {
    showToast(`Не удалось создать консультацию: ${error.message}`, 'error');
  }
};

// --- АБОНЕМЕНТЫ / ПОСЕЩАЕМОСТЬ ---
window.loadAdminSubscriptions = async function() {
  if (typeof window.loadSubscriptions === 'function') {
    return window.loadSubscriptions();
  }
};

// --- ДОСТИЖЕНИЯ ---
window.loadAdminAchievements = async function() {
  const container = document.getElementById('adminAchievementsList');
  if (!container) return;
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Загрузка достижений...</div>';
  try {
    const response = await requestJson('/achievements');
    const achievements = response.data || [];
    if (!achievements.length) {
      container.innerHTML = '<div style="text-align:center; padding:60px 0; color:var(--text-muted);">Достижений пока нет.</div>';
      return;
    }
    container.innerHTML = achievements.map(achievement => {
      const studentName = achievement.student_name || 'Ученик';
      const fallbackUrl = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(studentName) + '&background=2C473E&color=B0D182';
      const avatarUrl = achievement.student_avatar_url && typeof window.getStudentImageUrl === 'function' ? window.getStudentImageUrl({ image_url: achievement.student_avatar_url }) : null;
      return `<div class="directory-row" style="align-items:center;">
      <div class="dir-identity" style="flex:1.5;">
        <div class="dir-avatar" style="background:var(--bg-lighter); color:var(--pal-light-green);">${achievement.is_collective ? '<iconify-icon icon="solar:cup-star-bold-duotone"></iconify-icon>' : `<img src="${avatarUrl || fallbackUrl}" alt="${escapeCalendarText(studentName)}" loading="lazy" onerror="this.onerror=null; this.src='${fallbackUrl}'">`}</div>
        <div><div class="dir-name">${escapeCalendarText(achievement.title)}</div><div class="dir-meta">${achievement.is_collective ? 'Коллективное' : escapeCalendarText(studentName)}${achievement.event_date ? ` • ${escapeCalendarText(achievement.event_date)}` : ''}</div></div>
      </div>
      <div style="flex:2;"><div class="dir-meta">${escapeCalendarText(achievement.description || 'Без описания')}</div>${achievement.place ? `<div class="dir-name">${escapeCalendarText(achievement.place)}</div>` : ''}</div>
      <div class="dir-actions">${achievement.file_url ? `<a class="btn-icon" title="Открыть файл" href="${achievement.file_url}" target="_blank" rel="noopener"><iconify-icon icon="solar:document-text-bold-duotone"></iconify-icon></a>` : ''}${achievement.video_url ? `<a class="btn-icon" title="Открыть видео" href="${achievement.video_url}" target="_blank" rel="noopener"><iconify-icon icon="solar:videocamera-record-bold-duotone"></iconify-icon></a>` : ''}</div>
    </div>`;
    }).join('');
  } catch (error) {
    container.innerHTML = `<div style="padding:32px; color:var(--pal-accent-red);">Не удалось загрузить достижения: ${escapeCalendarText(error.message)}</div>`;
  }
};

window.openAchievementModal = async function() {
  document.getElementById('addAchievementModal').classList.add('active');
  const select = document.getElementById('achievementStudent');
  if (!select || select.dataset.loaded) return;
  try {
    const response = await requestJson('/education/students');
    select.innerHTML = (response.data || []).map(student => {
      const name = student.full_name || `${student.first_name || ''} ${student.last_name || ''}`.trim() || student.email;
      return `<option value="${student.id}">${escapeCalendarText(name)}</option>`;
    }).join('');
    select.dataset.loaded = 'true';
  } catch (error) {
    showToast(`Не удалось загрузить учеников: ${error.message}`, 'error');
  }
};

window.saveAchievement = async function() {
  const saveButton = document.querySelector('#addAchievementModal .modal-header .btn-primary');
  const title = document.getElementById('achievementTitle').value.trim();
  const target = document.querySelector('input[name="achievementTarget"]:checked')?.value || 'student';
  const studentId = document.getElementById('achievementStudent').value;
  if (!title || (target === 'student' && !studentId)) {
    showToast('Укажите название и ученика.', 'warning');
    return;
  }
  if (saveButton) saveButton.disabled = true;
  const formData = new FormData();
  formData.append('title', title);
  const description = document.getElementById('achievementDescription').value.trim();
  const place = document.getElementById('achievementPlace').value.trim();
  const eventDate = document.getElementById('achievementDate').value;
  if (description) formData.append('description', description);
  if (place) formData.append('place', place);
  if (eventDate) formData.append('event_date', eventDate);
  formData.append('assignment_type', target === 'all' ? 'collective' : 'individual');
  if (target === 'student') formData.append('student_id', studentId);
  const file = document.getElementById('achievementFile').files[0];
  if (file) formData.append('file', file);
  try {
    await requestFormData('/achievements/create', formData, { method: 'POST' });
    document.getElementById('addAchievementModal').classList.remove('active');
    document.getElementById('achievementFile').value = '';
    showToast('Достижение добавлено', 'success');
    try {
      await loadAdminAchievements();
    } catch (error) {
      showToast(`Достижение создано, но список не обновился: ${error.message}`, 'warning');
    }
  } catch (error) {
    showToast(`Не удалось добавить достижение: ${error.message}${error.detail ? ` (${error.detail})` : ''}`, 'error');
  } finally {
    if (saveButton) saveButton.disabled = false;
  }
};
