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
        
        this.mouseX = null;
        this.mouseY = null;
        
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
        this.tooltipData = [];
        this._hoveredExperiment = null;
        this.calculateScales();
        this.drawAxes();
        if (this.showLandLine) {
            this.drawLandProfile();
        }
        if (this.showRoadLine) {
            this.drawRoadProfile();
        }
        // --- SHADING BETWEEN PROFILES ---
        if (this.showLandLine && this.showRoadLine) {
            this.drawShadingBetweenProfiles();
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
        // crosshair را فقط اینجا بکش
        if (this.mouseX !== null && this.mouseY !== null) {
            this.drawCrosshair(this.mouseX, this.mouseY);
            this.showProfileTooltip(this.mouseX, this.mouseY);
            this.showTooltip(this.mouseX, this.mouseY);
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
        // سایه ضخیم زیر پروفیل
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 0; i < points.length - 1; i++) {
            const p0 = points[i];
            const p1 = points[i + 1];
            const cp1x = p0.x + (p1.x - p0.x) / 3;
            const cp1y = p0.y;
            const cp2x = p0.x + 2 * (p1.x - p0.x) / 3;
            const cp2y = p1.y;
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p1.x, p1.y);
        }
        ctx.strokeStyle = 'rgba(56,249,215,0.18)';
        ctx.lineWidth = 16;
        ctx.shadowColor = '#38f9d7';
        ctx.shadowBlur = 24;
        ctx.stroke();
        // خط اصلی پروفیل
        ctx.shadowBlur = 0;
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#43e97b');
        grad.addColorStop(1, '#38f9d7');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 4.5;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 0; i < points.length - 1; i++) {
            const p0 = points[i];
            const p1 = points[i + 1];
            const cp1x = p0.x + (p1.x - p0.x) / 3;
            const cp1y = p0.y;
            const cp2x = p0.x + 2 * (p1.x - p0.x) / 3;
            const cp2y = p1.y;
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p1.x, p1.y);
        }
        ctx.stroke();
        // نقاط مهم (شروع، پایان، مینیمم، ماکزیمم)
        const minY = Math.min(...points.map(p => p.y));
        const maxY = Math.max(...points.map(p => p.y));
        const specialPoints = [0, points.length-1];
        points.forEach((p, i) => {
            if (specialPoints.includes(i) || p.y === minY || p.y === maxY) {
                ctx.save();
                // دایره gradient
                let gradCircle = ctx.createRadialGradient(p.x, p.y, 2, p.x, p.y, 12);
                gradCircle.addColorStop(0, '#fff');
                gradCircle.addColorStop(1, p.y === minY || p.y === maxY ? '#fdcb6e' : '#00b894');
                ctx.beginPath();
                ctx.arc(p.x, p.y, 12, 0, 2 * Math.PI);
                ctx.fillStyle = gradCircle;
                ctx.globalAlpha = 0.95;
                ctx.shadowColor = gradCircle;
                ctx.shadowBlur = 18;
                ctx.fill();
                ctx.shadowBlur = 0;
                ctx.globalAlpha = 1;
                // border دو رنگ
                ctx.lineWidth = 3.5;
                ctx.strokeStyle = '#fff';
                ctx.stroke();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = '#222';
                ctx.stroke();
                ctx.restore();
                // ذخیره مختصات برای تولتیپ
                if (!this.profileTooltipData) this.profileTooltipData = [];
                this.profileTooltipData.push({
                    x: p.x, y: p.y, r: 15, realX: p.realX, realY: p.realY,
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
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2.5;
        // افکت glow
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 18;
        // رسم پیکسل آزمایش
        const pixelSize = 16;
        ctx.beginPath();
        ctx.arc(x, y, pixelSize / 2, 0, 2 * Math.PI);
        ctx.globalAlpha = 0.98;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
        ctx.stroke();
        // افکت hover (اگر موس روی این نقطه است)
        if (this._hoveredExperiment && this._hoveredExperiment.x === x && this._hoveredExperiment.y === y) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(x, y, pixelSize / 2 + 4, 0, 2 * Math.PI);
            ctx.strokeStyle = '#1976d2';
            ctx.lineWidth = 3.5;
            ctx.shadowColor = '#1976d2';
            ctx.shadowBlur = 16;
            ctx.globalAlpha = 0.7;
            ctx.stroke();
            ctx.restore();
        }
        // اضافه کردن نشانگر برای آزمایش‌های تایید شده
        if (experiment.approval_status === 1) {
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = '#28a745';
            ctx.fill();
        }
        ctx.restore();
        // ذخیره اطلاعات برای تولتیپ
        if (!this.tooltipData) this.tooltipData = [];
        this.tooltipData.push({
            x: x,
            y: y,
            width: pixelSize,
            height: pixelSize,
            data: {
                experiment: experiment,
                layer: layer
            }
        });
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
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;
        // بروزرسانی نمایش مختصات
        const realX = this.xMin + (this.mouseX - this.margin - 50) / (this.xScale * this.zoomLevel);
        const realY = this.yMax - (this.mouseY - this.margin) / (this.yScale * this.zoomLevel);
        document.getElementById('xinput').value = realX.toFixed(3);
        document.getElementById('yinput').value = realY.toFixed(3);
        // فقط render را صدا بزن تا crosshair و بقیه اجزا دوباره کشیده شوند
        this.render();
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
            this._hoveredExperiment = {x: hoveredItem.x, y: hoveredItem.y};
            const data = hoveredItem.data;
            const experiment = data.experiment;
            const layer = data.layer;
            // رنگ border بر اساس وضعیت
            const statusColors = {
                0: '#ffc107', 1: '#17a2b8', 2: '#28a745', 3: '#dc3545'
            };
            const statusColor = statusColors[experiment.status] || '#888';
            tooltip.innerHTML = `
                <div style="display:flex;align-items:center;gap:6px;">
                  <span style="font-size:18px;">🧪</span>
                  <span style="font-weight:bold;color:${statusColor};font-size:15px;">آزمایش ${experiment.experiment_type}</span>
                </div>
                <div style="font-size:13px;color:#555;">لایه: <b>${layer.name}</b></div>
                <div style="font-size:13px;color:#555;">کیلومتر: <b>${experiment.kilometer_start} - ${experiment.kilometer_end}</b></div>
                <div style="font-size:13px;color:#555;">تاریخ: <b>${experiment.request_date || 'نامشخص'}</b></div>
                <div style="font-size:13px;color:#555;">وضعیت: <b>${this.getStatusText(experiment.status)}</b></div>
                ${experiment.description ? `<div style='font-size:12px;color:#888;margin-top:2px;'>${experiment.description}</div>` : ''}
                <div style='width:0;height:0;border:8px solid transparent;border-top:10px solid ${statusColor};margin:0 auto;'></div>
            `;
            tooltip.style.display = 'block';
            tooltip.style.left = (x + 18) + 'px';
            tooltip.style.top = (y - 24) + 'px';
            tooltip.style.border = `2.5px solid ${statusColor}`;
            tooltip.style.borderRadius = '12px';
            tooltip.style.boxShadow = '0 6px 24px rgba(0,0,0,0.18)';
            tooltip.style.animation = 'fadeInTooltip 0.22s';
        } else {
            this._hoveredExperiment = null;
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

    drawCrosshair(x, y) {
        const ctx = this.canvas.ctx;
        ctx.save();
        ctx.strokeStyle = 'rgba(44,62,80,0.18)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, this.height);
        ctx.moveTo(0, y);
        ctx.lineTo(this.width, y);
        ctx.stroke();
        ctx.restore();
    }

    // --- SHADING BETWEEN LAND AND ROAD PROFILES ---
    drawShadingBetweenProfiles() {
        const profileData = this.projectData.profile_data;
        if (!profileData.land_points || !profileData.road_points) return;
        if (profileData.land_points.length !== profileData.road_points.length) return;
        const ctx = this.canvas.ctx;
        ctx.save();
        for (let i = 0; i < profileData.land_points.length - 1; i++) {
            const landA = profileData.land_points[i];
            const landB = profileData.land_points[i + 1];
            const roadA = profileData.road_points[i];
            const roadB = profileData.road_points[i + 1];
            const x1 = this.transformX(landA.x);
            const x2 = this.transformX(landB.x);
            const yLand1 = this.transformY(landA.y);
            const yLand2 = this.transformY(landB.y);
            const yRoad1 = this.transformY(roadA.y);
            const yRoad2 = this.transformY(roadB.y);

            // تعیین نوع (خاکبرداری یا خاکریزی)
            const isExcavation = yLand1 < yRoad1 && yLand2 < yRoad2; // زمین بالاتر از جاده
            const isEmbankment = yLand1 > yRoad1 && yLand2 > yRoad2; // جاده بالاتر از زمین

            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x1, yLand1);
            ctx.lineTo(x2, yLand2);
            ctx.lineTo(x2, yRoad2);
            ctx.lineTo(x1, yRoad1);
            ctx.closePath();
            ctx.clip();

            // هاشور مورب با زاویه ۴۵ درجه
            let color = 'rgba(200,200,200,0.15)';
            if (isExcavation) color = 'rgba(255,0,0,0.5)';
            if (isEmbankment) color = 'rgba(0,100,255,0.4)';
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.2;
            // خطوط مورب ۴۵ درجه
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            const minY = Math.min(yLand1, yRoad1, yLand2, yRoad2);
            const maxY = Math.max(yLand1, yRoad1, yLand2, yRoad2);
            for (let d = minX - (maxY - minY); d < maxX + (maxY - minY); d += 8) {
                ctx.beginPath();
                ctx.moveTo(d, minY - 20);
                ctx.lineTo(d + (maxY - minY) + 40, maxY + 20);
                ctx.stroke();
            }
            ctx.restore();
        }
        ctx.restore();
    }
} 