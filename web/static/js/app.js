/**
 * 主应用JavaScript
 * 科普视频自动化制作系统
 */

// ==================== 全局工具函数 ====================

/**
 * 格式化时间
 * @param {string} isoString - ISO时间字符串
 * @returns {string} 格式化后的时间
 */
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 显示提示消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success, error, warning, info）
 * @param {number} duration - 显示时长（毫秒）
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} fixed top-4 right-4 z-50 max-w-md`;
    toast.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 font-bold">✕</button>
        </div>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, duration);
}

/**
 * 确认对话框
 * @param {string} message - 确认消息
 * @returns {Promise<boolean>} 用户选择
 */
function confirm(message) {
    return window.confirm(message);
}

// ==================== API工具函数 ====================

/**
 * API请求基础URL
 */
const API_BASE_URL = '/api';

/**
 * 通用API请求函数
 * @param {string} url - 请求URL
 * @param {object} options - 请求选项
 * @returns {Promise<object>} 响应数据
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || '请求失败');
        }

        return data;
    } catch (error) {
        console.error('API请求失败:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

/**
 * GET请求
 */
async function apiGet(url) {
    return apiRequest(url, { method: 'GET' });
}

/**
 * POST请求
 */
async function apiPost(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * PUT请求
 */
async function apiPut(url, data) {
    return apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

/**
 * DELETE请求
 */
async function apiDelete(url) {
    return apiRequest(url, { method: 'DELETE' });
}

// ==================== WebSocket工具函数 ====================

/**
 * 连接WebSocket并监听进度
 * @param {string} taskId - 任务ID
 * @param {Function} onProgress - 进度回调函数
 * @param {Function} onComplete - 完成回调函数
 * @param {Function} onError - 错误回调函数
 * @returns {WebSocket} WebSocket实例
 */
function connectWebSocket(taskId, onProgress, onComplete, onError) {
    const ws = new WebSocket(`ws://${window.location.host}/ws/progress/${taskId}`);

    ws.onopen = () => {
        console.log('WebSocket连接成功');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.status === 'completed') {
            onComplete?.(data);
        } else if (data.status === 'failed') {
            onError?.(data);
        } else {
            onProgress?.(data);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        onError?.({ error: 'WebSocket连接失败' });
    };

    ws.onclose = () => {
        console.log('WebSocket连接关闭');
    };

    return ws;
}

// ==================== 表单工具函数 ====================

/**
 * 收集表单数据
 * @param {HTMLFormElement} form - 表单元素
 * @returns {object} 表单数据对象
 */
function collectFormData(form) {
    const formData = new FormData(form);
    const data = {};

    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }

    return data;
}

/**
 * 填充表单数据
 * @param {HTMLFormElement} form - 表单元素
 * @param {object} data - 数据对象
 */
function fillFormData(form, data) {
    for (const [key, value] of Object.entries(data)) {
        const input = form.elements[key];
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = value;
            } else if (input.type === 'radio') {
                if (input.value === value) {
                    input.checked = true;
                }
            } else {
                input.value = value;
            }
        }
    }
}

// ==================== 文件上传工具函数 ====================

/**
 * 上传文件
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<object>} 上传结果
 */
async function uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const progress = (e.loaded / e.total) * 100;
                onProgress?.(progress);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                const response = JSON.parse(xhr.responseText);
                resolve(response);
            } else {
                reject(new Error('上传失败'));
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('网络错误'));
        });

        xhr.open('POST', '/api/materials/upload');
        xhr.send(formData);
    });
}

// ==================== 拖拽上传工具函数 ====================

/**
 * 初始化拖拽上传区域
 * @param {HTMLElement} element - 拖拽区域元素
 * @param {Function} onDrop - 文件放下回调
 */
function initDragDrop(element, onDrop) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.classList.add('dragover');
    });

    element.addEventListener('dragleave', () => {
        element.classList.remove('dragover');
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            onDrop?.(files[0]);
        }
    });
}

// ==================== 页面初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('科普视频自动化制作系统已加载');

    // 全局错误处理
    window.addEventListener('error', (e) => {
        console.error('全局错误:', e.error);
        showToast('发生错误，请刷新页面重试', 'error');
    });

    // 全局Promise错误处理
    window.addEventListener('unhandledrejection', (e) => {
        console.error('未处理的Promise错误:', e.reason);
        showToast('请求失败，请稍后重试', 'error');
    });
});

// ==================== 导出 ====================

// 将工具函数暴露给全局作用域
window.appUtils = {
    formatTime,
    formatFileSize,
    showToast,
    confirm,
    apiGet,
    apiPost,
    apiPut,
    apiDelete,
    connectWebSocket,
    collectFormData,
    fillFormData,
    uploadFile,
    initDragDrop,
};
