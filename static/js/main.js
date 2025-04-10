// main.js - 行政服务平台主要JavaScript文件

// 当文档加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('行政服务平台前端脚本已加载');
    
    // 设置闪现消息自动消失
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 3000);
    });
    
    // 其他初始化代码可以放在这里
});

// 表单验证函数
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
} 