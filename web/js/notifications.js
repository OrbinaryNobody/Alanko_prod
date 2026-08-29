/**
 * Alanko CRM - Unified Notifications & Dialogs System
 * Provides sleek, branded modal dialogs (Confirm, Prompt, Alert) and floating corner Toasts.
 */

(function () {
  'use strict';

  // Inject CSS styles for Toasts and Dialogs
  const styleEl = document.createElement('style');
  styleEl.id = 'alanko-notifications-styles';
  styleEl.textContent = `
    /* ================= TOASTS SYSTEM ================= */
    .alanko-toast-container {
      position: fixed;
      bottom: 28px;
      right: 28px;
      z-index: 999999;
      display: flex;
      flex-direction: column-reverse;
      gap: 12px;
      max-width: 420px;
      width: calc(100vw - 40px);
      pointer-events: none;
    }

    .alanko-toast {
      pointer-events: auto;
      background: rgba(14, 18, 16, 0.95);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 14px 18px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 1px rgba(255, 255, 255, 0.15);
      display: flex;
      align-items: flex-start;
      gap: 14px;
      transform: translateX(120%);
      opacity: 0;
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.35s ease, margin 0.25s ease;
      position: relative;
      overflow: hidden;
    }

    .alanko-toast.show {
      transform: translateX(0);
      opacity: 1;
    }

    .alanko-toast.hide {
      transform: translateX(120%);
      opacity: 0;
      margin-bottom: -60px;
    }

    .alanko-toast-icon-wrap {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      flex-shrink: 0;
      margin-top: 1px;
    }

    .alanko-toast.toast-success {
      border-color: rgba(176, 209, 130, 0.25);
    }
    .alanko-toast.toast-success .alanko-toast-icon-wrap {
      background: rgba(176, 209, 130, 0.15);
      color: #B0D182;
    }

    .alanko-toast.toast-error {
      border-color: rgba(239, 108, 108, 0.25);
    }
    .alanko-toast.toast-error .alanko-toast-icon-wrap {
      background: rgba(239, 108, 108, 0.15);
      color: #EF6C6C;
    }

    .alanko-toast.toast-warning {
      border-color: rgba(242, 201, 76, 0.25);
    }
    .alanko-toast.toast-warning .alanko-toast-icon-wrap {
      background: rgba(242, 201, 76, 0.15);
      color: #F2C94C;
    }

    .alanko-toast.toast-info {
      border-color: rgba(130, 177, 255, 0.25);
    }
    .alanko-toast.toast-info .alanko-toast-icon-wrap {
      background: rgba(130, 177, 255, 0.15);
      color: #82B1FF;
    }

    .alanko-toast-content {
      flex: 1;
      min-width: 0;
    }

    .alanko-toast-title {
      font-weight: 700;
      font-size: 0.92rem;
      color: #FFFFFF;
      margin-bottom: 2px;
    }

    .alanko-toast-message {
      font-size: 0.86rem;
      color: #D8DCE5;
      line-height: 1.45;
      word-break: break-word;
    }

    .alanko-toast-close {
      background: transparent;
      border: none;
      color: #8E95A5;
      cursor: pointer;
      font-size: 1.1rem;
      padding: 2px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      transition: all 0.2s;
      margin-left: 4px;
      flex-shrink: 0;
    }

    .alanko-toast-close:hover {
      color: #FFFFFF;
      background: rgba(255, 255, 255, 0.08);
    }

    .alanko-toast-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      height: 2px;
      background: currentColor;
      opacity: 0.4;
      width: 100%;
      transform-origin: left;
      animation: toastProgress linear forwards;
    }

    @keyframes toastProgress {
      from { transform: scaleX(1); }
      to { transform: scaleX(0); }
    }

    /* ================= UNIFIED DIALOG MODAL ================= */
    .alanko-dialog-overlay {
      position: fixed;
      inset: 0;
      background: rgba(5, 6, 10, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      z-index: 999998;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      opacity: 0;
      visibility: hidden;
      transition: all 0.25s ease;
    }

    .alanko-dialog-overlay.active {
      opacity: 1;
      visibility: visible;
    }

    .alanko-dialog-card {
      width: 100%;
      max-width: 440px;
      background: #0E1311;
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 24px 64px rgba(0, 0, 0, 0.65), 0 0 1px rgba(255, 255, 255, 0.2);
      display: flex;
      flex-direction: column;
      transform: scale(0.94) translateY(12px);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .alanko-dialog-overlay.active .alanko-dialog-card {
      transform: scale(1) translateY(0);
    }

    .alanko-dialog-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }

    .alanko-dialog-badge {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
    }

    .alanko-dialog-card.type-danger .alanko-dialog-badge {
      background: rgba(239, 108, 108, 0.14);
      color: #EF6C6C;
      box-shadow: 0 0 20px rgba(239, 108, 108, 0.2);
    }

    .alanko-dialog-card.type-warning .alanko-dialog-badge {
      background: rgba(242, 201, 76, 0.14);
      color: #F2C94C;
      box-shadow: 0 0 20px rgba(242, 201, 76, 0.2);
    }

    .alanko-dialog-card.type-success .alanko-dialog-badge {
      background: rgba(176, 209, 130, 0.14);
      color: #B0D182;
      box-shadow: 0 0 20px rgba(176, 209, 130, 0.2);
    }

    .alanko-dialog-card.type-info .alanko-dialog-badge {
      background: rgba(130, 177, 255, 0.14);
      color: #82B1FF;
      box-shadow: 0 0 20px rgba(130, 177, 255, 0.2);
    }

    .alanko-dialog-close-btn {
      background: transparent;
      border: none;
      color: #8E95A5;
      cursor: pointer;
      font-size: 1.25rem;
      padding: 6px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }

    .alanko-dialog-close-btn:hover {
      color: #FFFFFF;
      background: rgba(255, 255, 255, 0.08);
    }

    .alanko-dialog-title {
      font-size: 1.3rem;
      font-weight: 700;
      color: #FFFFFF;
      margin-bottom: 8px;
      line-height: 1.3;
    }

    .alanko-dialog-message {
      font-size: 0.92rem;
      color: #8E95A5;
      line-height: 1.55;
      margin-bottom: 20px;
    }

    .alanko-dialog-input-wrap {
      margin-bottom: 24px;
    }

    .alanko-dialog-input {
      width: 100%;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 12px 16px;
      color: #FFFFFF;
      font-family: inherit;
      font-size: 0.95rem;
      outline: none;
      transition: all 0.2s;
      box-sizing: border-box;
    }

    .alanko-dialog-input:focus {
      border-color: #B0D182;
      background: rgba(255, 255, 255, 0.08);
      box-shadow: 0 0 16px rgba(176, 209, 130, 0.15);
    }

    .alanko-dialog-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
    }

    .alanko-dialog-btn {
      padding: 12px 24px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.9rem;
      font-family: inherit;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
      border: none;
    }

    .alanko-dialog-btn-secondary {
      background: rgba(255, 255, 255, 0.06);
      color: #FFFFFF;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .alanko-dialog-btn-secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      transform: translateY(-1px);
    }

    .alanko-dialog-btn-primary {
      background: #B0D182;
      color: #05060A;
    }

    .alanko-dialog-btn-primary:hover {
      background: #C2E396;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(176, 209, 130, 0.3);
    }

    .alanko-dialog-btn-danger {
      background: rgba(239, 108, 108, 0.2);
      color: #FF8F8F;
      border: 1px solid rgba(239, 108, 108, 0.4);
    }

    .alanko-dialog-btn-danger:hover {
      background: #EF6C6C;
      color: #FFFFFF;
      border-color: #EF6C6C;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(239, 108, 108, 0.35);
    }
  `;
  document.head.appendChild(styleEl);

  // 1. Toast Container
  let toastContainer = null;
  function getToastContainer() {
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'alanko-toast-container';
      document.body.appendChild(toastContainer);
    }
    return toastContainer;
  }

  const iconMap = {
    success: 'solar:check-circle-bold-duotone',
    error: 'solar:danger-triangle-bold-duotone',
    warning: 'solar:shield-warning-bold-duotone',
    info: 'solar:info-circle-bold-duotone',
    danger: 'solar:trash-bin-trash-bold-duotone',
  };

  /**
   * Show a non-blocking toast notification in the corner of the screen
   * @param {string} message 
   * @param {'success'|'error'|'warning'|'info'} type 
   * @param {number} duration in ms (default 3500)
   */
  window.showToast = function (message, type = 'info', duration = 3500) {
    if (!message) return;
    const container = getToastContainer();
    const iconName = iconMap[type] || iconMap.info;

    let titleText = '';
    if (type === 'success') titleText = 'Успешно';
    else if (type === 'error') titleText = 'Ошибка';
    else if (type === 'warning') titleText = 'Внимание';
    else titleText = 'Информация';

    const toast = document.createElement('div');
    toast.className = `alanko-toast toast-${type}`;
    toast.innerHTML = `
      <div class="alanko-toast-icon-wrap">
        <iconify-icon icon="${iconName}"></iconify-icon>
      </div>
      <div class="alanko-toast-content">
        <div class="alanko-toast-title">${titleText}</div>
        <div class="alanko-toast-message">${escapeHtml(message)}</div>
      </div>
      <button type="button" class="alanko-toast-close" title="Закрыть">
        <iconify-icon icon="solar:close-circle-bold"></iconify-icon>
      </button>
      <div class="alanko-toast-progress" style="animation-duration: ${duration}ms;"></div>
    `;

    const closeToast = () => {
      if (toast.classList.contains('hide')) return;
      toast.classList.remove('show');
      toast.classList.add('hide');
      setTimeout(() => {
        toast.remove();
      }, 350);
    };

    toast.querySelector('.alanko-toast-close').onclick = closeToast;

    container.appendChild(toast);
    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    const timer = setTimeout(closeToast, duration);
    toast.addEventListener('mouseenter', () => clearTimeout(timer));

    return { close: closeToast };
  };

  /**
   * Helper dialog overlay creator
   */
  let currentDialogResolve = null;
  let dialogOverlay = null;

  function getDialogOverlay() {
    if (!dialogOverlay) {
      dialogOverlay = document.createElement('div');
      dialogOverlay.className = 'alanko-dialog-overlay';
      dialogOverlay.id = 'alankoGlobalDialogOverlay';
      dialogOverlay.innerHTML = `
        <div class="alanko-dialog-card" id="alankoGlobalDialogCard">
          <div class="alanko-dialog-header">
            <div class="alanko-dialog-badge" id="alankoDialogBadge">
              <iconify-icon icon="solar:danger-triangle-bold-duotone" id="alankoDialogIcon"></iconify-icon>
            </div>
            <button type="button" class="alanko-dialog-close-btn" id="alankoDialogCloseBtn" title="Закрыть">
              <iconify-icon icon="solar:close-circle-bold"></iconify-icon>
            </button>
          </div>
          <h3 class="alanko-dialog-title" id="alankoDialogTitle">Подтвердите действие</h3>
          <p class="alanko-dialog-message" id="alankoDialogMessage"></p>
          <div class="alanko-dialog-input-wrap" id="alankoDialogInputWrap" style="display: none;">
            <input type="text" class="alanko-dialog-input" id="alankoDialogInput">
          </div>
          <div class="alanko-dialog-actions" id="alankoDialogActions">
            <button type="button" class="alanko-dialog-btn alanko-dialog-btn-secondary" id="alankoDialogCancelBtn">Отмена</button>
            <button type="button" class="alanko-dialog-btn alanko-dialog-btn-primary" id="alankoDialogConfirmBtn">Подтвердить</button>
          </div>
        </div>
      `;
      document.body.appendChild(dialogOverlay);

      // Close on background click
      dialogOverlay.addEventListener('click', (e) => {
        if (e.target === dialogOverlay) {
          closeDialog(null);
        }
      });

      // Close on Escape or confirm on Enter
      document.addEventListener('keydown', (e) => {
        if (!dialogOverlay.classList.contains('active')) return;
        if (e.key === 'Escape') {
          closeDialog(null);
        } else if (e.key === 'Enter' && e.target.id === 'alankoDialogInput') {
          e.preventDefault();
          document.getElementById('alankoDialogConfirmBtn').click();
        }
      });
    }
    return dialogOverlay;
  }

  function closeDialog(result) {
    if (dialogOverlay) {
      dialogOverlay.classList.remove('active');
    }
    if (currentDialogResolve) {
      const resolve = currentDialogResolve;
      currentDialogResolve = null;
      resolve(result);
    }
  }

  /**
   * Show a unified Confirm dialog (returns Promise<boolean>)
   * @param {Object} options
   * @param {string} options.title
   * @param {string} options.message
   * @param {'danger'|'warning'|'info'|'success'} [options.type='danger']
   * @param {string} [options.confirmText='Подтвердить']
   * @param {string} [options.cancelText='Отмена']
   */
  window.showConfirm = function (options = {}) {
    const {
      title = 'Вы уверены?',
      message = 'Это действие нельзя отменить.',
      type = 'danger',
      confirmText = type === 'danger' ? 'Да, удалить' : 'Подтвердить',
      cancelText = 'Отмена',
    } = options;

    return new Promise((resolve) => {
      const overlay = getDialogOverlay();
      currentDialogResolve = resolve;

      const card = overlay.querySelector('#alankoGlobalDialogCard');
      card.className = `alanko-dialog-card type-${type}`;

      const iconEl = overlay.querySelector('#alankoDialogIcon');
      iconEl.setAttribute('icon', iconMap[type] || iconMap.danger);

      overlay.querySelector('#alankoDialogTitle').textContent = title;
      overlay.querySelector('#alankoDialogMessage').textContent = message;
      overlay.querySelector('#alankoDialogInputWrap').style.display = 'none';

      const cancelBtn = overlay.querySelector('#alankoDialogCancelBtn');
      cancelBtn.textContent = cancelText;
      cancelBtn.style.display = 'inline-flex';
      cancelBtn.onclick = () => closeDialog(false);

      const confirmBtn = overlay.querySelector('#alankoDialogConfirmBtn');
      confirmBtn.textContent = confirmText;
      confirmBtn.className = `alanko-dialog-btn ${type === 'danger' ? 'alanko-dialog-btn-danger' : 'alanko-dialog-btn-primary'}`;
      confirmBtn.onclick = () => closeDialog(true);

      overlay.querySelector('#alankoDialogCloseBtn').onclick = () => closeDialog(false);

      overlay.classList.add('active');
      confirmBtn.focus();
    });
  };

  /**
   * Show a unified Prompt dialog (returns Promise<string|null>)
   * @param {Object} options
   * @param {string} options.title
   * @param {string} [options.message]
   * @param {string} [options.placeholder]
   * @param {string} [options.defaultValue='']
   * @param {'info'|'warning'|'success'|'danger'} [options.type='info']
   * @param {string} [options.confirmText='Сохранить']
   * @param {string} [options.cancelText='Отмена']
   * @param {boolean} [options.required=false]
   */
  window.showPrompt = function (options = {}) {
    let title = typeof options === 'string' ? options : options.title || 'Введите данные';
    let message = options.message || '';
    let placeholder = options.placeholder || '';
    let defaultValue = options.defaultValue || '';
    let type = options.type || 'info';
    let confirmText = options.confirmText || 'Сохранить';
    let cancelText = options.cancelText || 'Отмена';
    let required = !!options.required;

    return new Promise((resolve) => {
      const overlay = getDialogOverlay();
      currentDialogResolve = resolve;

      const card = overlay.querySelector('#alankoGlobalDialogCard');
      card.className = `alanko-dialog-card type-${type}`;

      const iconEl = overlay.querySelector('#alankoDialogIcon');
      iconEl.setAttribute('icon', iconMap[type] || 'solar:pen-bold-duotone');

      overlay.querySelector('#alankoDialogTitle').textContent = title;
      const msgEl = overlay.querySelector('#alankoDialogMessage');
      msgEl.textContent = message;
      msgEl.style.display = message ? 'block' : 'none';

      const inputWrap = overlay.querySelector('#alankoDialogInputWrap');
      inputWrap.style.display = 'block';
      const input = overlay.querySelector('#alankoDialogInput');
      input.value = defaultValue;
      input.placeholder = placeholder;

      const cancelBtn = overlay.querySelector('#alankoDialogCancelBtn');
      cancelBtn.textContent = cancelText;
      cancelBtn.style.display = 'inline-flex';
      cancelBtn.onclick = () => closeDialog(null);

      const confirmBtn = overlay.querySelector('#alankoDialogConfirmBtn');
      confirmBtn.textContent = confirmText;
      confirmBtn.className = `alanko-dialog-btn alanko-dialog-btn-primary`;
      confirmBtn.onclick = () => {
        const val = input.value.trim();
        if (required && !val) {
          input.focus();
          window.showToast('Пожалуйста, заполните это поле', 'warning');
          return;
        }
        closeDialog(val);
      };

      overlay.querySelector('#alankoDialogCloseBtn').onclick = () => closeDialog(null);

      overlay.classList.add('active');
      setTimeout(() => {
        input.focus();
        input.select();
      }, 50);
    });
  };

  /**
   * Show a unified Alert modal dialog (returns Promise<void>)
   */
  window.showAlertModal = function (title, message = '', type = 'info') {
    return new Promise((resolve) => {
      const overlay = getDialogOverlay();
      currentDialogResolve = resolve;

      const card = overlay.querySelector('#alankoGlobalDialogCard');
      card.className = `alanko-dialog-card type-${type}`;

      const iconEl = overlay.querySelector('#alankoDialogIcon');
      iconEl.setAttribute('icon', iconMap[type] || iconMap.info);

      overlay.querySelector('#alankoDialogTitle').textContent = title;
      const msgEl = overlay.querySelector('#alankoDialogMessage');
      msgEl.textContent = message;
      msgEl.style.display = message ? 'block' : 'none';
      overlay.querySelector('#alankoDialogInputWrap').style.display = 'none';

      overlay.querySelector('#alankoDialogCancelBtn').style.display = 'none';

      const confirmBtn = overlay.querySelector('#alankoDialogConfirmBtn');
      confirmBtn.textContent = 'Понятно';
      confirmBtn.className = `alanko-dialog-btn alanko-dialog-btn-primary`;
      confirmBtn.onclick = () => closeDialog(true);

      overlay.querySelector('#alankoDialogCloseBtn').onclick = () => closeDialog(true);

      overlay.classList.add('active');
      confirmBtn.focus();
    });
  };

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
})();
