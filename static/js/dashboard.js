import { Canvas } from './canvas.js';
import { YAxisCanvas } from './yaxiscanvas.js';
import { XAxisCanvas } from './xaxiscanvas.js';

export class ProjectDashboard {
    constructor({ containerId, projectData, width, height, margin }) {
        this.containerId = containerId;
        this.projectData = projectData;
        this.width = width;
        this.height = height;
        this.margin = margin;
        this.container = document.getElementById(containerId);
        
        // تنظیمات نمایش
        this.showRoadLine = true;
        this.showLandLine = true;
        this.showLayerLine = true;
        this.showStructures = true;
        this.showExperiments = true;
        
        // تنظیمات زوم و پن
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        
        // تنظیمات نمودار
        this.xScale = 1;
        this.yScale = 1;
        this.xOffset = 0;
        this.yOffset = 0;
        
        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.render();
    }

    setupCanvas() {
        // ایجاد canvas اصلی
        this.canvas = new Canvas({
            containerId: this.containerId,
            width: this.width,
            height: this.height,
            margin: this.margin,
            start_kilometer: this.projectData.start_kilometer,
            end_kilometer: this.projectData.end_kilometer
        });

        // ایجاد محور Y
        this.yAxis = new YAxisCanvas({
            canvasId: 'yAxisCanvas',
            height: this.height,
            width: 50,
            margin: this.margin,
            yunit: 43
        });

        // ایجاد محور X
        this.xAxis = new XAxisCanvas({
            canvasId: 'xAxisCanvas',
            width: this.width - 50, // کم کردن عرض محور Y
            height: 30,
            margin: this.margin,
            xunit: 100
        });
    }

    setupEventListeners() {
        const mainCanvas = document.getElementById('mainCanvas');
        
        // رویدادهای موس
        mainCanvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        mainCanvas.addEventListener('click', (e) => this.handleClick(e));
        mainCanvas.addEventListener('wheel', (e) => this.handleWheel(e));
        
        // رویدادهای لمسی
        mainCanvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        mainCanvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
    }

    render() {
        this.canvas.clear();
        this.profileTooltipData = [];
        this.calculateScales();
        this.drawAxes();
        if (this.showLandLine) {
            this.drawLandProfile();
        }
        if (this.showRoadLine) {
            this.drawRoadProfile();
        }
        if (this.showLayerLine) {
            this.drawLayers();
        }
        if (this.showStructures) {
            this.drawStructures();
        }
        if (this.showExperiments) {
            this.drawExperiments();
        }
    }

    calculateScales() {
        const profileData = this.projectData.profile_data;
        if (!profileData.land_points || profileData.land_points.length === 0) {
            return;
        }

        // محاسبه محدوده داده‌ها
        const xValues = profileData.land_points.map(p => p.x);
        const yValues = [...profileData.land_points.map(p => p.y), ...profileData.road_points.map(p => p.y)];
        
        this.xMin = Math.min(...xValues);
        this.xMax = Math.max(...xValues);
        this.yMin = Math.min(...yValues);
        this.yMax = Math.max(...yValues);
        
        // اضافه کردن حاشیه
        const xRange = this.xMax - this.xMin;
        const yRange = this.yMax - this.yMin;
        const xMargin = xRange * 0.1;
        const yMargin = yRange * 0.1;
        
        this.xMin -= xMargin;
        this.xMax += xMargin;
        this.yMin -= yMargin;
        this.yMax += yMargin;
        
        // محاسبه مقیاس‌ها
        const canvasWidth = this.width - this.margin * 2 - 50; // کم کردن عرض محور Y
        const canvasHeight = this.height - this.margin * 2 - 30; // کم کردن ارتفاع محور X
        
        this.xScale = canvasWidth / (this.xMax - this.xMin);
        this.yScale = canvasHeight / (this.yMax - this.yMin);
    }

    drawAxes() {
        // بروزرسانی محور X
        const xLabels = [];
        const step = (this.xMax - this.xMin) / 10;
        for (let i = 0; i <= 10; i++) {
            const value = this.xMin + step * i;
            xLabels.push(`${value.toFixed(1)}km`);
        }
        this.xAxis.update(xLabels);
        
        // بروزرسانی محور Y
        const yLabels = [];
        const yStep = (this.yMax - this.yMin) / 10;
        for (let i = 0; i <= 10; i++) {
            const value = this.yMin + yStep * i;
            yLabels.push(`${value.toFixed(1)}m`);
        }
        this.yAxis.update(yLabels);
    }

    drawLandProfile() {
        const profileData = this.projectData.profile_data;
        if (!profileData.land_points || profileData.land_points.length === 0) return;
        const points = profileData.land_points.map(point => ({
            x: this.transformX(point.x),
            y: this.transformY(point.y),
            realX: point.x,
            realY: point.y
        }));
        const ctx = this.canvas.ctx;
        ctx.save();
        // گرادینت سبز-آبی برای پروفیل زمین
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#43e97b');
        grad.addColorStop(1, '#38f9d7');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 4;
        ctx.shadowColor = '#38f9d7';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        // خطوط نرم با Bezier
        for (let i = 1; i < points.length - 2; i++) {
            const xc = (points[i].x + points[i + 1].x) / 2;
            const yc = (points[i].y + points[i + 1].y) / 2;
            ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        ctx.quadraticCurveTo(
            points[points.length - 2].x,
            points[points.length - 2].y,
            points[points.length - 1].x,
            points[points.length - 1].y
        );
        ctx.stroke();
        ctx.shadowBlur = 0;
        // نقاط مهم (شروع، پایان، مینیمم، ماکزیمم)
        const minY = Math.min(...points.map(p => p.y));
        const maxY = Math.max(...points.map(p => p.y));
        const specialPoints = [0, points.length-1];
        points.forEach((p, i) => {
            if (specialPoints.includes(i) || p.y === minY || p.y === maxY) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 8, 0, 2 * Math.PI);
                ctx.fillStyle = p.y === minY || p.y === maxY ? '#fdcb6e' : '#00b894';
                ctx.shadowColor = ctx.fillStyle;
                ctx.shadowBlur = 16;
                ctx.fill();
                ctx.shadowBlur = 0;
                // ذخیره مختصات برای تولتیپ
                if (!this.profileTooltipData) this.profileTooltipData = [];
                this.profileTooltipData.push({
                    x: p.x, y: p.y, r: 10, realX: p.realX, realY: p.realY,
                    type: specialPoints.includes(i) ? (i === 0 ? 'شروع' : 'پایان') : (p.y === minY ? 'مینیمم' : 'ماکزیمم')
                });
            }
        });
        ctx.restore();
    }

    drawRoadProfile() {
        const profileData = this.projectData.profile_data;
        if (!profileData.road_points || profileData.road_points.length === 0) return;
        const points = profileData.road_points.map(point => ({
            x: this.transformX(point.x),
            y: this.transformY(point.y)
        }));
        const ctx = this.canvas.ctx;
        ctx.save();
        // گرادینت آبی-بنفش برای پروفیل جاده
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#00c6ff');
        grad.addColorStop(1, '#0072ff');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 3;
        ctx.shadowColor = '#00c6ff';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
        // نقاط مهم (شروع و پایان)
        [0, points.length-1].forEach(idx => {
            ctx.beginPath();
            ctx.arc(points[idx].x, points[idx].y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = '#0984e3';
            ctx.shadowColor = '#0984e3';
            ctx.shadowBlur = 10;
            ctx.fill();
            ctx.shadowBlur = 0;
        });
        ctx.restore();
    }

    drawLayers() {
        this.projectData.layers.forEach(layer => {
            const layerY = this.transformY(layer.order_from_top * 10); // تبدیل ترتیب لایه به ارتفاع
            const layerHeight = layer.thickness_cm * this.yScale;
            
            // رسم خط لایه
            this.canvas.drawLayerLine([{
                x: this.margin + 50,
                y: layerY,
                t: layer.thickness_cm
            }]);
            
            // رسم نماد لایه
            this.drawLayerSymbol(layer, layerY);
        });
    }

    drawLayerSymbol(layer, y) {
        const ctx = this.canvas.ctx;
        const x = this.margin + 50;
        
        ctx.save();
        
        // انتخاب رنگ بر اساس وضعیت
        const colors = {
            0: '#6c757d', // شروع نشده
            1: '#ffc107', // در حال انجام
            2: '#28a745'  // تکمیل شده
        };
        
        ctx.fillStyle = colors[layer.status] || '#6c757d';
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        
        // رسم نماد بر اساس نوع لایه
        if (layer.state === 1) { // ثابت
            // مستطیل
            ctx.fillRect(x - 20, y - 5, 40, 10);
            ctx.strokeRect(x - 20, y - 5, 40, 10);
        } else { // متغیر
            // متوازی‌الاضلاع
            ctx.beginPath();
            ctx.moveTo(x - 20, y - 5);
            ctx.lineTo(x + 20, y - 5);
            ctx.lineTo(x + 15, y + 5);
            ctx.lineTo(x - 25, y + 5);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
        }
        
        // نوشتن نام لایه
        ctx.fillStyle = '#000';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(layer.name, x, y - 10);
        
        ctx.restore();
    }

    drawStructures() {
        this.projectData.structures.forEach(structure => {
            const x = this.transformX(structure.kilometer_location);
            const y = this.height / 2; // وسط نمودار
            
            this.drawStructureSymbol(structure, x, y);
        });
    }

    drawStructureSymbol(structure, x, y) {
        const ctx = this.canvas.ctx;
        
        ctx.save();
        
        // انتخاب رنگ بر اساس نوع ابنیه
        const colors = {
            'پل': '#007bff',
            'آبرو': '#17a2b8',
            'تونل': '#6f42c1'
        };
        
        ctx.fillStyle = colors[structure.name] || '#6c757d';
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        
        // رسم نماد ابنیه
        if (structure.name.includes('پل')) {
            // نماد پل
            ctx.beginPath();
            ctx.moveTo(x - 15, y);
            ctx.lineTo(x + 15, y);
            ctx.moveTo(x - 10, y - 10);
            ctx.lineTo(x + 10, y - 10);
            ctx.moveTo(x - 5, y - 20);
            ctx.lineTo(x + 5, y - 20);
            ctx.stroke();
        } else if (structure.name.includes('آبرو')) {
            // نماد آبرو
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
        } else {
            // نماد عمومی
            ctx.fillRect(x - 10, y - 10, 20, 20);
            ctx.strokeRect(x - 10, y - 10, 20, 20);
        }
        
        // نوشتن نام ابنیه
        ctx.fillStyle = '#000';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(structure.name, x, y + 25);
        
        ctx.restore();
    }

    drawExperiments() {
        this.projectData.layers.forEach(layer => {
            layer.experiments.forEach(experiment => {
                const x = this.transformX(experiment.kilometer_start);
                const y = this.transformY(layer.order_from_top * 10);
                
                this.drawExperimentPixel(experiment, x, y, layer);
            });
        });
    }

    drawExperimentPixel(experiment, x, y, layer) {
        const ctx = this.canvas.ctx;
        
        ctx.save();
        
        // انتخاب رنگ بر اساس وضعیت
        const colors = {
            0: '#ffc107', // در انتظار
            1: '#17a2b8', // در حال انجام
            2: '#28a745', // تکمیل شده
            3: '#dc3545'  // رد شده
        };
        
        ctx.fillStyle = colors[experiment.status] || '#ffc107';
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        
        // رسم پیکسل آزمایش
        const pixelSize = 8;
        ctx.fillRect(x - pixelSize/2, y - pixelSize/2, pixelSize, pixelSize);
        ctx.strokeRect(x - pixelSize/2, y - pixelSize/2, pixelSize, pixelSize);
        
        // اضافه کردن نشانگر برای آزمایش‌های تایید شده
        if (experiment.approval_status === 1) {
            ctx.fillStyle = '#28a745';
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
        
        // ذخیره اطلاعات برای تولتیپ
        this.addTooltipData(x, y, experiment, layer);
    }

    addTooltipData(x, y, experiment, layer) {
        if (!this.tooltipData) {
            this.tooltipData = [];
        }
        
        this.tooltipData.push({
            x: x,
            y: y,
            width: 8,
            height: 8,
            data: {
                experiment: experiment,
                layer: layer
            }
        });
    }

    transformX(x) {
        return this.margin + 50 + (x - this.xMin) * this.xScale * this.zoomLevel + this.panX;
    }

    transformY(y) {
        return this.margin + (this.yMax - y) * this.yScale * this.zoomLevel + this.panY;
    }

    handleMouseMove(e) {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        // بروزرسانی نمایش مختصات
        const realX = this.xMin + (x - this.margin - 50) / (this.xScale * this.zoomLevel);
        const realY = this.yMax - (y - this.margin) / (this.yScale * this.zoomLevel);
        document.getElementById('xinput').value = realX.toFixed(3);
        document.getElementById('yinput').value = realY.toFixed(3);
        // نمایش تولتیپ نقاط پروفیل
        this.showProfileTooltip(x, y);
        // نمایش تولتیپ آزمایش‌ها
        this.showTooltip(x, y);
    }

    showProfileTooltip(x, y) {
        const tooltip = document.getElementById('tooltip');
        if (!this.profileTooltipData) return;
        const hovered = this.profileTooltipData.find(pt =>
            Math.abs(x - pt.x) < pt.r && Math.abs(y - pt.y) < pt.r
        );
        if (hovered) {
            tooltip.innerHTML = `
                <strong>نقطه ${hovered.type}</strong><br>
                کیلومتر: ${hovered.realX.toFixed(3)}<br>
                ارتفاع: ${hovered.realY.toFixed(2)}
            `;
            tooltip.style.display = 'block';
            tooltip.style.left = (x + 12) + 'px';
            tooltip.style.top = (y - 12) + 'px';
        } else {
            tooltip.style.display = 'none';
        }
    }

    showTooltip(x, y) {
        const tooltip = document.getElementById('tooltip');
        
        if (!this.tooltipData) return;
        
        const hoveredItem = this.tooltipData.find(item => 
            x >= item.x - item.width/2 && 
            x <= item.x + item.width/2 && 
            y >= item.y - item.height/2 && 
            y <= item.y + item.height/2
        );
        
        if (hoveredItem) {
            const data = hoveredItem.data;
            const experiment = data.experiment;
            const layer = data.layer;
            
            const tooltipContent = `
                <strong>آزمایش ${experiment.experiment_type}</strong><br>
                لایه: ${layer.name}<br>
                کیلومتر: ${experiment.kilometer_start} - ${experiment.kilometer_end}<br>
                تاریخ: ${experiment.request_date || 'نامشخص'}<br>
                وضعیت: ${this.getStatusText(experiment.status)}<br>
                ${experiment.description ? `توضیحات: ${experiment.description}` : ''}
            `;
            
            tooltip.innerHTML = tooltipContent;
            tooltip.style.display = 'block';
            tooltip.style.left = (x + 10) + 'px';
            tooltip.style.top = (y - 10) + 'px';
        } else {
            tooltip.style.display = 'none';
        }
    }

    getStatusText(status) {
        const statuses = {
            0: 'در انتظار',
            1: 'در حال انجام',
            2: 'تکمیل شده',
            3: 'رد شده'
        };
        return statuses[status] || 'نامشخص';
    }

    handleClick(e) {
        // در آینده می‌توان برای باز کردن جزئیات آزمایش استفاده کرد
    }

    handleWheel(e) {
        e.preventDefault();
        
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoomLevel *= delta;
        this.zoomLevel = Math.max(0.1, Math.min(5, this.zoomLevel));
        
        this.render();
    }

    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
    }

    handleTouchMove(e) {
        if (!this.touchStartX || !this.touchStartY) return;
        
        e.preventDefault();
        
        const deltaX = e.touches[0].clientX - this.touchStartX;
        const deltaY = e.touches[0].clientY - this.touchStartY;
        
        this.panX += deltaX;
        this.panY += deltaY;
        
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
        
        this.render();
    }

    // متدهای کنترل نمایش
    toggleRoadLine() {
        this.showRoadLine = !this.showRoadLine;
        this.render();
    }

    toggleLandLine() {
        this.showLandLine = !this.showLandLine;
        this.render();
    }

    toggleLayerLine() {
        this.showLayerLine = !this.showLayerLine;
        this.render();
    }

    toggleStructures() {
        this.showStructures = !this.showStructures;
        this.render();
    }

    toggleExperiments() {
        this.showExperiments = !this.showExperiments;
        this.render();
    }

    // متدهای زوم
    zoomIn() {
        this.zoomLevel *= 1.2;
        this.zoomLevel = Math.min(5, this.zoomLevel);
        this.render();
    }

    zoomOut() {
        this.zoomLevel *= 0.8;
        this.zoomLevel = Math.max(0.1, this.zoomLevel);
        this.render();
    }

    resetZoom() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        this.render();
    }
} 