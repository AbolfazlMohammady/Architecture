// توابع کمکی برای داشبورد پروژه

export class DashboardUtils {
    // تبدیل مختصات صفحه به مختصات واقعی
    static screenToReal(x, y, xMin, xMax, yMin, yMax, canvasWidth, canvasHeight, margin, zoomLevel, panX, panY) {
        const realX = xMin + (x - margin - 50) / (canvasWidth / (xMax - xMin)) / zoomLevel - panX;
        const realY = yMax - (y - margin) / (canvasHeight / (yMax - yMin)) / zoomLevel - panY;
        return { x: realX, y: realY };
    }

    // تبدیل مختصات واقعی به مختصات صفحه
    static realToScreen(x, y, xMin, xMax, yMin, yMax, canvasWidth, canvasHeight, margin, zoomLevel, panX, panY) {
        const screenX = margin + 50 + (x - xMin) * (canvasWidth / (xMax - xMin)) * zoomLevel + panX;
        const screenY = margin + (yMax - y) * (canvasHeight / (yMax - yMin)) * zoomLevel + panY;
        return { x: screenX, y: screenY };
    }

    // محاسبه فاصله بین دو نقطه
    static distance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }

    // بررسی اینکه آیا نقطه در محدوده مشخص شده است
    static isPointInBounds(x, y, bounds) {
        return x >= bounds.x && x <= bounds.x + bounds.width && 
               y >= bounds.y && y <= bounds.y + bounds.height;
    }

    // فرمت کردن اعداد
    static formatNumber(num, decimals = 2) {
        return Number(num).toFixed(decimals);
    }

    // فرمت کردن تاریخ
    static formatDate(dateString) {
        if (!dateString) return 'نامشخص';
        const date = new Date(dateString);
        return date.toLocaleDateString('fa-IR');
    }

    // تولید رنگ بر اساس وضعیت
    static getStatusColor(status, type = 'experiment') {
        const colors = {
            experiment: {
                0: '#ffc107', // در انتظار
                1: '#17a2b8', // در حال انجام
                2: '#28a745', // تکمیل شده
                3: '#dc3545'  // رد شده
            },
            layer: {
                0: '#6c757d', // شروع نشده
                1: '#ffc107', // در حال انجام
                2: '#28a745'  // تکمیل شده
            },
            structure: {
                0: '#6c757d', // شروع نشده
                1: '#ffc107', // در حال انجام
                2: '#28a745', // تکمیل شده
                3: '#dc3545', // متوقف شده
                4: '#6c757d'  // لغو شده
            }
        };
        
        return colors[type][status] || '#6c757d';
    }

    // تولید متن وضعیت
    static getStatusText(status, type = 'experiment') {
        const texts = {
            experiment: {
                0: 'در انتظار',
                1: 'در حال انجام',
                2: 'تکمیل شده',
                3: 'رد شده'
            },
            layer: {
                0: 'شروع نشده',
                1: 'در حال انجام',
                2: 'تکمیل شده'
            },
            structure: {
                0: 'شروع نشده',
                1: 'در حال انجام',
                2: 'تکمیل شده',
                3: 'متوقف شده',
                4: 'لغو شده'
            }
        };
        
        return texts[type][status] || 'نامشخص';
    }

    // تولید نماد برای نوع ابنیه
    static getStructureSymbol(structureName) {
        if (structureName.includes('پل')) {
            return 'bridge';
        } else if (structureName.includes('آبرو')) {
            return 'culvert';
        } else if (structureName.includes('تونل')) {
            return 'tunnel';
        } else {
            return 'general';
        }
    }

    // بررسی محدودیت‌های لایه‌بندی
    static checkLayerConstraints(layers) {
        const constraints = [];
        
        for (let i = 0; i < layers.length - 1; i++) {
            const currentLayer = layers[i];
            const nextLayer = layers[i + 1];
            
            // اگر لایه پایینی تکمیل نشده، لایه بالایی نمی‌تواند درخواست آزمایش داشته باشد
            if (currentLayer.status !== 2 && nextLayer.experiments.length > 0) {
                constraints.push({
                    type: 'layer_order',
                    message: `لایه ${nextLayer.name} نمی‌تواند آزمایش داشته باشد تا زمانی که لایه ${currentLayer.name} تکمیل نشده است`,
                    layerId: nextLayer.id,
                    severity: 'warning'
                });
            }
        }
        
        return constraints;
    }

    // محاسبه پیشرفت پروژه
    static calculateProjectProgress(layers) {
        if (layers.length === 0) return 0;
        
        const completedLayers = layers.filter(layer => layer.status === 2).length;
        return (completedLayers / layers.length) * 100;
    }

    // تولید داده‌های نمونه برای تست
    static generateSampleData() {
        return {
            land_points: [
                { x: 30, y: 0 },
                { x: 31, y: 2 },
                { x: 32, y: -1 },
                { x: 33, y: 3 },
                { x: 34, y: 1 },
                { x: 35, y: 4 },
                { x: 36, y: 0 },
                { x: 37, y: 2 },
                { x: 38, y: -2 },
                { x: 39, y: 1 },
                { x: 40, y: 3 }
            ],
            road_points: [
                { x: 30, y: 5 },
                { x: 31, y: 7 },
                { x: 32, y: 4 },
                { x: 33, y: 8 },
                { x: 34, y: 6 },
                { x: 35, y: 9 },
                { x: 36, y: 5 },
                { x: 37, y: 7 },
                { x: 38, y: 3 },
                { x: 39, y: 6 },
                { x: 40, y: 8 }
            ]
        };
    }

    // اعتبارسنجی داده‌های پروژه
    static validateProjectData(projectData) {
        const errors = [];
        
        if (!projectData.profile_data || !projectData.profile_data.land_points) {
            errors.push('داده‌های پروفیل موجود نیست');
        }
        
        if (!projectData.layers || projectData.layers.length === 0) {
            errors.push('لایه‌ای برای پروژه تعریف نشده است');
        }
        
        if (projectData.start_kilometer >= projectData.end_kilometer) {
            errors.push('کیلومتر شروع باید کمتر از کیلومتر پایان باشد');
        }
        
        return errors;
    }

    // بهینه‌سازی عملکرد نمودار
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // تنظیم مقیاس خودکار
    static autoScale(data, canvasWidth, canvasHeight, margin) {
        if (!data || data.length === 0) {
            return { xScale: 1, yScale: 1, xMin: 0, xMax: 100, yMin: 0, yMax: 100 };
        }
        
        const xValues = data.map(p => p.x);
        const yValues = data.map(p => p.y);
        
        const xMin = Math.min(...xValues);
        const xMax = Math.max(...xValues);
        const yMin = Math.min(...yValues);
        const yMax = Math.max(...yValues);
        
        const xRange = xMax - xMin;
        const yRange = yMax - yMin;
        
        const xMargin = xRange * 0.1;
        const yMargin = yRange * 0.1;
        
        const adjustedXMin = xMin - xMargin;
        const adjustedXMax = xMax + xMargin;
        const adjustedYMin = yMin - yMargin;
        const adjustedYMax = yMax + yMargin;
        
        const xScale = (canvasWidth - margin * 2 - 50) / (adjustedXMax - adjustedXMin);
        const yScale = (canvasHeight - margin * 2 - 30) / (adjustedYMax - adjustedYMin);
        
        return {
            xScale,
            yScale,
            xMin: adjustedXMin,
            xMax: adjustedXMax,
            yMin: adjustedYMin,
            yMax: adjustedYMax
        };
    }
} 