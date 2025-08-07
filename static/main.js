// 文件路径: static/main.js (完整修正版)

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

            // 处理替换动作 (用于编辑)
            if (result.action === 'replace' && result.html && result.replace_target) {
                const oldElement = document.querySelector(result.replace_target);
                if (oldElement) {
                    oldElement.outerHTML = result.html;
                    const newElement = document.querySelector(result.replace_target);
                    if (newElement) {
                        lucide.createIcons({nodes: [newElement]});
                        const newCard = newElement.querySelector('.countdown-card-new');
                        if (newCard && typeof setProgress === 'function') {
                            setProgress(newCard);
                        }
                    }
                }
            }
            // 处理添加动作
            else if (result.html && result.target_container) {
                const container = document.querySelector(result.target_container);
                if (container) {
                    const action = result.action === 'append' ? 'beforeend' : 'afterbegin';
                    container.insertAdjacentHTML(action, result.html);
                    const newElement = action === 'beforeend' ? container.lastElementChild : container.firstElementChild;
                    lucide.createIcons({nodes: [newElement]});
                } else {
                    setTimeout(() => window.location.reload(), 800);
                }
                form.reset();
            }

            // 处理页面重载指令
            if (result.reload) {
                setTimeout(() => window.location.reload(), 500);
                return;
            }

            // 处理局部内容更新 (例如统计数据)
            if (result.updates) {
                for (const key in result.updates) {
                    const updateInfo = result.updates[key];
                    const targetElement = document.querySelector(updateInfo.target_id);
                    if (targetElement) {
                        targetElement.textContent = updateInfo.value;
                    }
                }
            }

            // 处理移除元素
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

    if (!deleteUrl) {
        console.error('Delete button is missing data-delete-url attribute.');
        showToast('无法删除，页面元素配置不正确。', 'error');
        return;
    }

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

            // --- BUG修复 #1：在这里添加处理 updates 的逻辑 ---
            if (result.updates) {
                for (const key in result.updates) {
                    const updateInfo = result.updates[key];
                    const targetElement = document.querySelector(updateInfo.target_id);
                    if (targetElement) {
                        targetElement.textContent = updateInfo.value;
                    }
                }
            }

            if (removeTargetSelector) {
                const elementToRemove = document.querySelector(removeTargetSelector);
                if (elementToRemove) {
                    elementToRemove.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                    elementToRemove.style.opacity = '0';
                    elementToRemove.style.transform = 'scale(0.95)';
                    setTimeout(() => elementToRemove.remove(), 400);
                }
            }
            if (result.reload) {
                setTimeout(() => window.location.reload(), 500);
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
        // --- BUG修复 #2：使用正确的函数名 ---
        submitAjaxForm(event.target);
    }
});