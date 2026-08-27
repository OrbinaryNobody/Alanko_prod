// Админская интеграция с API

// --- ТАБЫ ---
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const tabId = e.target.getAttribute('data-tab');
      handleTabChange(tabId);
    });
  });
  
  // Инициализация при загрузке
  const activeTab = document.querySelector('.tab-btn.active');
  if (activeTab) {
    handleTabChange(activeTab.getAttribute('data-tab'));
  }
});

function handleTabChange(tabId) {
  if (tabId === 'tab-students') loadAdminStudents();
  if (tabId === 'tab-teachers') loadAdminTeachers();
  if (tabId === 'tab-programs') loadAdminPrograms();
  if (tabId === 'tab-consultations') loadAdminConsultations();
  if (tabId === 'tab-achievements') loadAdminAchievements();
  if (tabId === 'tab-subscriptions') loadAdminSubscriptions();
}

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
    row.innerHTML = `
      <div class="group-info">
        <div class="group-name"></div>
        <div class="group-students">Статус: ${group.status || 'active'}</div>
      </div>`;
    row.querySelector('.group-name').textContent = group.title || 'Без названия';
    groupsList.appendChild(row);
  });
  const addRow = document.createElement('div');
  addRow.className = 'group-row';
  addRow.innerHTML = '<button class="btn-sm primary create-program-group" type="button"><iconify-icon icon="solar:add-circle-bold"></iconify-icon> Создать группу</button>';
  addRow.querySelector('.create-program-group').onclick = () => createProgramGroup(card, program);
  groupsList.appendChild(addRow);
}

async function createProgramGroup(card, program) {
  const title = window.prompt(`Название группы для программы «${program.title}»:`);
  if (!title || !title.trim()) return;
  try {
    await requestJson('/education/groups', {
      method: 'POST',
      body: JSON.stringify({ title: title.trim(), description: null, program_id: program.id }),
    });
    const groupsResponse = await requestJson('/education/groups');
    renderProgramGroups(card, program, groupsResponse.data || []);
  } catch (error) {
    alert(`Не удалось создать группу: ${error.message}`);
  }
}

// --- УЧЕНИКИ ---
window.loadAdminStudents = async function() {
  const container = document.querySelector('#tab-students .directory-list');
  if (!container) return;
  container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Загрузка учеников...</div>';
  
  try {
    const res = await apiFetch('/education/students');
    const payload = await res.json();
    const students = payload.data || [];
    
    if (!students.length) {
      container.innerHTML = '<div style="padding: 32px; color: var(--text-muted);">Учеников пока нет.</div>';
      return;
    }
    
    container.innerHTML = students.map(st => `
      <div class="directory-row" onclick="openStudentDossier('${st.full_name || st.email}', '', '')">
        <div class="dir-identity">
          <div class="dir-avatar">
            <img src="${st.avatar_url || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(st.full_name || st.email)}" alt="">
          </div>
          <div class="dir-info">
            <div style="display: flex; flex-direction: column; gap: 4px;">
              <span class="dir-name" style="line-height: 1;">${st.full_name || st.email}</span>
            </div>
            <span class="dir-meta">${st.group_name || 'Без группы'}</span>
          </div>
        </div>
        <div class="dir-actions">
          <button class="btn-icon-danger" onclick="event.stopPropagation(); deleteStudentAdmin(${st.id})" style="padding: 8px;">
            <iconify-icon icon="solar:trash-bin-trash-bold"></iconify-icon>
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div style="padding: 32px; color: red;">Ошибка: ${err.message}</div>`;
  }
};

window.deleteStudentAdmin = async function(id) {
  if (!confirm('Удалить ученика?')) return;
  try {
    const res = await apiFetch(`/accounts/students/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Ошибка удаления');
    loadAdminStudents();
  } catch (err) {
    alert(err.message);
  }
};

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
      <div class="directory-row" onclick="openTeacherDossier()">
        <div class="dir-identity">
          <div class="dir-avatar">
            <img src="${t.avatar_url || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(t.full_name || t.email)}" alt="">
          </div>
          <div class="dir-info">
            <span class="dir-name">${t.full_name || t.email}</span>
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div style="padding: 32px; color: red;">Ошибка: ${err.message}</div>`;
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
window.loadAdminConsultations = async function() {
  try {
    const res = await apiFetch('/consultations/admin/days');
    if (res.ok) {
      const data = await res.json();
      console.log('Consultations loaded:', data);
    }
  } catch(e) {}
};

// --- АБОНЕМЕНТЫ / ПОСЕЩАЕМОСТЬ ---
window.loadAdminSubscriptions = async function() {
  try {
    const res = await apiFetch('/attendance/admin/subscriptions');
    if (res.ok) {
      const data = await res.json();
      console.log('Subscriptions loaded:', data);
    }
  } catch(e) {}
};

// --- ДОСТИЖЕНИЯ ---
window.loadAdminAchievements = async function() {
  try {
    const res = await apiFetch('/achievements');
    if (res.ok) {
      const data = await res.json();
      console.log('Achievements loaded:', data);
    }
  } catch(e) {}
};
