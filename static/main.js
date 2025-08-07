// 文件路径: static/main.js
const showToast = (message, category = 'info') => {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        console.error('Toast container element not found!');
        return;
    }

    const toastInfoMap = {
        success: {bg: 'bg-success', title: '成功'},
        danger: {bg: 'bg-danger', title: '错误'},
        error: {bg: 'bg-danger', title: '错误'},
        info: {bg: 'bg-primary', title: '提示'},
        warning: {bg: 'bg-warning', title: '警告'}
    };
    const toastInfo = toastInfoMap[category] || {bg: 'bg-secondary', title: '消息'};

    const toastId = `toast-${Date.now()}`;
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="5000">
          <div class="toast-header ${toastInfo.bg} text-white">
            <strong class="me-auto">${toastInfo.title}</strong>
            <small>刚刚</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
          <div class="toast-body">
            ${message}
          </div>
        </div>`;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const newToast = new bootstrap.Toast(toastElement);
    newToast.show();
    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
};


const submitAjaxForm = async (form) => {
    const modalInstance = form.closest('.modal') ? bootstrap.Modal.getInstance(form.closest('.modal')) : null;

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: form.method || 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || '操作成功！', 'success');
            if (modalInstance) modalInstance.hide();
            if (result.action === 'replace' && result.html && result.replace_target) {
                const oldElement = document.querySelector(result.replace_target);
                if (oldElement) {
                    // 用返回的新HTML替换掉旧的元素
                    oldElement.outerHTML = result.html;

                    // 由于元素被替换了，需要重新找到它来初始化新图标
                    const newElement = document.querySelector(result.replace_target);
                    if (newElement) {
                        lucide.createIcons({nodes: [newElement]});
                        // 找到新卡片里的计时器，并立即更新一次，避免视觉上的延迟
                        const newCard = newElement.querySelector('.countdown-card-new');
                        if (newCard && typeof setProgress === 'function') {
                            setProgress(newCard);
                        }
                    }
                }
                return; // 完成替换后，直接返回，不再执行下面的逻辑
            }
            if (result.reload) {
                setTimeout(() => window.location.reload(), 500);
                return;
            }

            if (result.html && result.target_container) {
                const container = document.querySelector(result.target_container);
                if (container) {
                    const action = result.action === 'append' ? 'beforeend' : 'afterbegin';
                    container.insertAdjacentHTML(action, result.html);
                    const newElement = action === 'beforeend' ? container.lastElementChild : container.firstElementChild;
                    const sibling = newElement.nextElementSibling;
                    const nodesToRender = sibling ? [newElement, sibling] : [newElement];
                    lucide.createIcons({nodes: nodesToRender});
                } else {
                    showToast('正在为您刷新页面以显示新的一天...', 'info');
                    setTimeout(() => window.location.reload(), 800);
                    return;
                }
                form.reset();
            }

            if (result.updates) {
                for (const key in result.updates) {
                    const updateInfo = result.updates[key];
                    const targetElement = document.querySelector(updateInfo.target_id);
                    if (targetElement) {
                        targetElement.textContent = updateInfo.value;
                    }
                }
            }

            const targetsToRemove = result.remove_target ? [result.remove_target] : (result.remove_targets || []);
            if (targetsToRemove.length > 0) {
                targetsToRemove.forEach(selector => {
                    const elementToRemove = document.querySelector(selector);
                    if (elementToRemove) {
                        elementToRemove.style.transition = 'opacity 0.3s ease';
                        elementToRemove.style.opacity = '0';
                        setTimeout(() => elementToRemove.remove(), 300);
                    }
                });
            }

        } else {
            showToast(result.message || '操作失败，请检查您的输入。', 'error');
            const errorDiv = form.querySelector('.error-message');
            if (errorDiv) {
                errorDiv.textContent = result.message;
                errorDiv.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Form submission failed:', error);
        showToast('提交失败，请检查您的网络连接。', 'error');
    }
};
const confirmDelete = async (event) => {
    event.preventDefault();
    const link = event.currentTarget;
    const deleteUrl = link.dataset.deleteUrl;
    const removeTargetSelector = link.dataset.removeTarget;
    const entityTitle = link.dataset.entityTitle || '此项目';

    if (!deleteUrl || !removeTargetSelector) {
        console.error('Delete button is missing data-delete-url or data-remove-target attribute.');
        showToast('无法删除，页面元素配置不正确。', 'error');
        return;
    }

    // 使用浏览器内置的确认框
    if (!confirm(`您确定要删除 “${entityTitle}” 吗？此操作无法撤销。`)) {
        return;
    }

    try {
        const response = await fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast(result.message || '删除成功！', 'success');
            const elementToRemove = document.querySelector(removeTargetSelector);
            if (elementToRemove) {
                // 添加一个平滑的淡出效果
                elementToRemove.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                elementToRemove.style.opacity = '0';
                elementToRemove.style.transform = 'scale(0.95)';
                setTimeout(() => elementToRemove.remove(), 400);
            }
        } else {
            showToast(result.message || '删除失败。', 'error');
        }
    } catch (error) {
        console.error('Deletion failed:', error);
        showToast('删除操作失败，请检查网络连接。', 'error');
    }
};

document.addEventListener('submit', function (event) {
    if (event.target.matches('form.ajax-form')) {
        event.preventDefault();
        handleAjaxFormSubmit(event.target);
    }
});
