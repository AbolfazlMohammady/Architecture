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
        
        // تنظیمات نمایش
        this.showRoadLine = true;
        this.showLandLine = true;
        this.showLayerLine = true;
        this.showStructures = true;
        this.showExperiments = true;
        
        // فیلترهای زمانی
        this.dateFilterStart = null;
        this.dateFilterEnd = null;
        
        // تنظیمات زوم و پن
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.zoomCenterX = null;
        this.zoomCenterY = null;
        this.originalXMin = null;
        this.originalXMax = null;
        this.originalYMin = null;
        this.originalYMax = null;
        
        // موقعیت موس
        this.mouseX = null;
        this.mouseY = null;
        
        // داده‌های تولتیپ
        this.profileTooltipData = [];
        this.tooltipData = [];
        this._hoveredExperiment = null;
        
        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.render();
    }

    setupCanvas() {
        // Calculate dynamic width based on project length
        const projectLength = this.projectData.end_kilometer - this.projectData.start_kilometer;
        const pxPerKm = 50; // 50px per km - نمودار بازتر با کیفیت بهتر
        const minWidth = 1200;
        this.dynamicWidth = Math.max(minWidth, Math.ceil(projectLength * pxPerKm));
        // Set the inner div width to match canvas for full scroll
        const chartInner = document.getElementById('chart-canvas-inner');
        if (chartInner) {
            chartInner.style.width = this.dynamicWidth + 'px';
        }

        // ایجاد canvas اصلی
        this.canvas = new Canvas({
            containerId: this.containerId,
            width: this.dynamicWidth,
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
            width: this.dynamicWidth - 50, // کم کردن عرض محور Y
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
        // mainCanvas.addEventListener('wheel', (e) => this.handleWheel(e)); // حذف زوم
        
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

        // ذخیره مقادیر اصلی برای reset zoom
        if (this.originalXMin === null) {
            // محور X باید از start_kilometer شروع شود نه از صفر
            this.originalXMin = this.projectData.start_kilometer;
            this.originalXMax = this.projectData.end_kilometer;
            
            const yValues = [...profileData.land_points.map(p => p.y), ...profileData.road_points.map(p => p.y)];
            const originalYMin = Math.min(...yValues);
            const originalYMax = Math.max(...yValues);
            const yRange = originalYMax - originalYMin;
            const yMargin = yRange * 0.1;
            
            this.originalYMin = originalYMin - yMargin;
            this.originalYMax = originalYMax + yMargin;
        }

        // استفاده از محدوده پروژه برای محور X - این مهم است!
        // محور X باید از start_kilometer شروع شود (مثل اکسل - از 6300 شروع می‌شود نه از صفر)
        // اعمال زوم
        const originalXRange = this.originalXMax - this.originalXMin;
        const xCenter = (this.originalXMin + this.originalXMax) / 2;
        const zoomedXRange = originalXRange / this.zoomLevel;
        // اطمینان از اینکه xMin از start_kilometer شروع می‌شود
        this.xMin = Math.max(this.projectData.start_kilometer, xCenter - zoomedXRange / 2);
        this.xMax = Math.min(this.projectData.end_kilometer, xCenter + zoomedXRange / 2);
        
        // محاسبه محدوده Y از داده‌ها
        const originalYRange = this.originalYMax - this.originalYMin;
        const yCenter = (this.originalYMin + this.originalYMax) / 2;
        const zoomedYRange = originalYRange / this.zoomLevel;
        this.yMin = yCenter - zoomedYRange / 2;
        this.yMax = yCenter + zoomedYRange / 2;
        
        // محاسبه مقیاس‌ها
        // استفاده از dynamicWidth که در setupCanvas محاسبه شده
        // transformX = margin + (x - xMin) * xScale
        // پس xScale باید بر اساس عرض قابل استفاده محاسبه شود
        // canvas.style.width = dynamicWidth است
        // اما باید عرض قابل استفاده را در نظر بگیریم (dynamicWidth - margin - 50 برای محور Y)
        const canvasWidth = (this.dynamicWidth || this.width) - this.margin - 50; // کم کردن margin و عرض محور Y
        const canvasHeight = this.height - this.margin * 2 - 30; // کم کردن ارتفاع محور X
        
        const currentXRange = this.xMax - this.xMin;
        this.xScale = canvasWidth / currentXRange;
        this.yScale = canvasHeight / (this.yMax - this.yMin);
    }

    drawAxes() {
        // بروزرسانی محور X
        const xLabels = [];
        const start = this.projectData.start_kilometer; // محور X باید از start_kilometer شروع شود
        const end = this.projectData.end_kilometer;
        const projectLength = end - start;
        
        // تنظیم step بر اساس طول پروژه - برای پروژه‌های بزرگ step بزرگتر
        let step;
        if (projectLength <= 5) {
            step = 0.5; // هر 500 متر برای پروژه‌های کوچک
        } else if (projectLength <= 20) {
            step = 1; // هر 1 کیلومتر
        } else if (projectLength <= 50) {
            step = 2; // هر 2 کیلومتر
        } else if (projectLength <= 100) {
            step = 5; // هر 5 کیلومتر
        } else {
            step = 10; // هر 10 کیلومتر برای پروژه‌های خیلی بزرگ
        }
        
        for (let km = start; km <= end + 0.0001; km += step) {
            xLabels.push(km);
        }
        this.xAxis.update(xLabels, start, end);
        
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
        ctx.strokeStyle = 'rgba(56,249,215,0.12)';
        ctx.lineWidth = 10;
        ctx.shadowColor = '#38f9d7';
        ctx.shadowBlur = 12; // کاهش هاله آبی
        ctx.stroke();
        // خط اصلی پروفیل - بهبود کیفیت
        ctx.shadowBlur = 0;
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#43e97b');
        grad.addColorStop(1, '#38f9d7');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
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
        // حذف رسم دایره‌های کوچک روی پروفیل زمین
        // (کد رسم دایره کاملاً حذف یا کامنت شود)
        ctx.restore();
    }

    drawRoadProfile() {
        const profileData = this.projectData.profile_data;
        if (!profileData.road_points || profileData.road_points.length === 0) return;
        const points = profileData.road_points.map(point => ({
            x: this.transformX(point.x),
            y: this.transformY(0) // همه نقاط جاده روی ارتفاع صفر
        }));
        const ctx = this.canvas.ctx;
        ctx.save();
        // گرادینت آبی-بنفش برای پروفیل جاده - بهبود کیفیت
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#00c6ff');
        grad.addColorStop(1, '#0072ff');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.shadowColor = '#00c6ff';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
        // نقاط مهم (شروع و پایان)
        // حذف رسم دایره‌های کوچک روی پروفیل جاده
        ctx.restore();
    }

    drawLayers() {
        const ctx = this.canvas.ctx;
        const profileData = this.projectData.profile_data;
        if (!profileData.road_points || profileData.road_points.length === 0) return;
        const layers = [...this.projectData.layers].sort((a, b) => a.order_from_top - b.order_from_top);
        if (!this.tooltipData) this.tooltipData = [];
        // فقط یکبار نام هر لایه را وسط بازه کل لایه یا وسط اولین executed_range بنویس
        for (let l = 0; l < layers.length; l++) {
            const layer = layers[l];
            let xLabel, yLabel;
            if (layer.executed_ranges && Array.isArray(layer.executed_ranges) && layer.executed_ranges.length > 0) {
                const range = layer.executed_ranges[0];
                xLabel = (this.transformX(range.start) + this.transformX(range.end)) / 2;
            } else {
                const x1 = this.transformX(profileData.road_points[0].x);
                const x2 = this.transformX(profileData.road_points[profileData.road_points.length - 1].x);
                xLabel = (x1 + x2) / 2;
            }
            yLabel = this.transformY(profileData.road_points[0].y) + l * 24 - 10;
            ctx.save();
            ctx.font = 'bold 14px Vazirmatn, Tahoma, Arial, sans-serif';
            ctx.fillStyle = '#222';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            // ctx.fillText(layer.name, xLabel, yLabel); // حذف نمایش اسم لایه
            ctx.restore();
        }
        for (let i = 0; i < profileData.road_points.length - 1; i++) {
            const x1 = this.transformX(profileData.road_points[i].x);
            const x2 = this.transformX(profileData.road_points[i + 1].x);
            let yTop1 = this.transformY(profileData.road_points[i].y);
            let yTop2 = this.transformY(profileData.road_points[i + 1].y);
            let yBase1 = yTop1;
            let yBase2 = yTop2;
            for (let l = 0; l < layers.length; l++) {
                const layer = layers[l];
                // ضخامت لایه‌ها را به صورت نسبی و با حداقل و حداکثر معقول محدود کن
                const canvasHeight = this.height - this.margin * 2 - 30;
                const maxLayerThicknessPx = canvasHeight * 0.12; // حداکثر 12 درصد ارتفاع نمودار برای نمایش بهتر
                const minLayerThicknessPx = 2;
                let thicknessPx1 = Math.max(Math.min(layer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                let thicknessPx2 = Math.max(Math.min(layer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                let yBottom1 = yBase1 + thicknessPx1;
                let yBottom2 = yBase2 + thicknessPx2;
                if (layer.status === 0) {
                    ctx.save();
                    ctx.strokeStyle = '#888';
                    ctx.beginPath();
                    ctx.moveTo(x1, yBase1);
                    ctx.lineTo(x2, yBase2);
                    ctx.lineTo(x2, yBottom2);
                    ctx.lineTo(x1, yBottom1);
                    ctx.closePath();
                    ctx.stroke();
                    ctx.restore();
                } else {
                    let fillColor = '#ffc107';
                    let borderColor = '#222';
                    let opacity = 0.7;
                    if (layer.status === 2) { fillColor = '#7ed957'; borderColor = 'transparent'; opacity = 0.85; } // حذف خط سبز دور هاشورها
                    else if (layer.status === 1) { fillColor = '#ffc107'; borderColor = '#ff9800'; opacity = 0.8; }
                    if (layer.state !== 1) {
                        fillColor = '#ff9800';
                        opacity = 0.08; // کاهش بیشتر opacity برای خط نارنجی (لایه متغیر) تا نازک‌تر دیده شود
                        // کاهش ضخامت لایه برای لایه‌های متغیر
                        const thicknessReduction = 0.25; // کاهش 75% ضخامت
                        thicknessPx1 = Math.max(thicknessPx1 * thicknessReduction, 1);
                        thicknessPx2 = Math.max(thicknessPx2 * thicknessReduction, 1);
                        // به‌روزرسانی yBottom بعد از کاهش ضخامت
                        yBottom1 = yBase1 + thicknessPx1;
                        yBottom2 = yBase2 + thicknessPx2;
                    }
                    let isNatural = layer.name.includes('بستر') || layer.name.includes('طبیعی');
                    ctx.save();
                    ctx.globalAlpha = opacity;
                    ctx.beginPath();
                    ctx.moveTo(x1, yBase1);
                    ctx.lineTo(x2, yBase2);
                    ctx.lineTo(x2, yBottom2);
                    ctx.lineTo(x1, yBottom1);
                    ctx.closePath();
                    if (layer.executed_ranges && Array.isArray(layer.executed_ranges) && layer.executed_ranges.length > 0) {
                        // رسم لایه‌ها در موقعیت دقیق خودشان (بر اساس executed_ranges)
                        for (const range of layer.executed_ranges) {
                            const xr1 = this.transformX(range.start);
                            const xr2 = this.transformX(range.end);
                            
                            // پیدا کردن yTop و yBottom برای این بازه - استفاده از interpolate
                            // interpolate برای موقعیت دقیق‌تر
                            let yTopStart, yTopEnd;
                            let yBottomStart, yBottomEnd;
                            
                            // interpolate برای range.start
                            let yStart = null;
                            for (let p = 0; p < profileData.road_points.length - 1; p++) {
                                const p1 = profileData.road_points[p];
                                const p2 = profileData.road_points[p + 1];
                                if (range.start >= p1.x && range.start <= p2.x) {
                                    // interpolate linear
                                    const t = (range.start - p1.x) / (p2.x - p1.x);
                                    yStart = p1.y + (p2.y - p1.y) * t;
                                    break;
                                }
                            }
                            if (yStart === null) {
                                // اگر خارج از محدوده بود، از نزدیک‌ترین نقطه استفاده کن
                                let minDist = Infinity;
                                for (let p = 0; p < profileData.road_points.length; p++) {
                                    const point = profileData.road_points[p];
                                    const dist = Math.abs(point.x - range.start);
                                    if (dist < minDist) {
                                        minDist = dist;
                                        yStart = point.y;
                                    }
                                }
                            }
                            yTopStart = this.transformY(yStart);
                            
                            // interpolate برای range.end
                            let yEnd = null;
                            for (let p = 0; p < profileData.road_points.length - 1; p++) {
                                const p1 = profileData.road_points[p];
                                const p2 = profileData.road_points[p + 1];
                                if (range.end >= p1.x && range.end <= p2.x) {
                                    // interpolate linear
                                    const t = (range.end - p1.x) / (p2.x - p1.x);
                                    yEnd = p1.y + (p2.y - p1.y) * t;
                                    break;
                                }
                            }
                            if (yEnd === null) {
                                // اگر خارج از محدوده بود، از نزدیک‌ترین نقطه استفاده کن
                                let minDist = Infinity;
                                for (let p = 0; p < profileData.road_points.length; p++) {
                                    const point = profileData.road_points[p];
                                    const dist = Math.abs(point.x - range.end);
                                    if (dist < minDist) {
                                        minDist = dist;
                                        yEnd = point.y;
                                    }
                                }
                            }
                            yTopEnd = this.transformY(yEnd);
                            
                            // محاسبه yBottom بر اساس yTop و لایه‌های قبلی
                            const canvasHeight = this.height - this.margin * 2 - 30;
                            let tempYBaseStart = yTopStart;
                            let tempYBaseEnd = yTopEnd;
                            for (let tempL = 0; tempL <= l; tempL++) {
                                const tempLayer = layers[tempL];
                                let tempThickness = Math.max(Math.min(tempLayer.thickness_cm * this.yScale / 100, canvasHeight * 0.12), 2);
                                // کاهش ضخامت برای لایه‌های متغیر
                                if (tempLayer.state !== 1) {
                                    tempThickness = Math.max(tempThickness * 0.25, 1); // کاهش 75% ضخامت
                                }
                                tempYBaseStart += tempThickness;
                                tempYBaseEnd += tempThickness;
                            }
                            yBottomStart = tempYBaseStart;
                            yBottomEnd = tempYBaseEnd;
                            
                            // رسم لایه در موقعیت دقیق
                            ctx.beginPath();
                            ctx.moveTo(xr1, yTopStart);
                            ctx.lineTo(xr2, yTopEnd);
                            ctx.lineTo(xr2, yBottomEnd);
                            ctx.lineTo(xr1, yBottomStart);
                            ctx.closePath();
                            ctx.fillStyle = fillColor;
                            ctx.fill();
                            
                            // stroke برای لایه - فقط اگر borderColor transparent نباشد
                            if (borderColor !== 'transparent') {
                                ctx.globalAlpha = 1;
                                ctx.lineWidth = 0.8;
                                ctx.strokeStyle = borderColor;
                                ctx.stroke();
                            }
                            
                            // --- اضافه کردن tooltipData برای لایه ---
                            if (!this.tooltipData) this.tooltipData = [];
                            this.tooltipData.push({
                                x: (xr1 + xr2) / 2,
                                y: (yTopStart + yBottomStart + yTopEnd + yBottomEnd) / 4,
                                width: Math.abs(xr2 - xr1),
                                height: Math.abs((yBottomStart + yBottomEnd) / 2 - (yTopStart + yTopEnd) / 2),
                                data: { type: 'layer', layer }
                            });
                        }
                        ctx.restore();
                    } else {
                        // رسم لایه کامل (بدون executed_ranges) - در موقعیت دقیق
                        ctx.fillStyle = fillColor;
                        ctx.fill();
                        ctx.globalAlpha = 1;
                        ctx.lineWidth = 0.8; // کاهش ضخامت خط
                        ctx.strokeStyle = borderColor;
                        ctx.stroke();
                        ctx.restore();
                    }
                }
                yBase1 = yBottom1;
                yBase2 = yBottom2;
            }
        }
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
        const profileData = this.projectData.profile_data;
        this.projectData.structures.forEach(structure => {
            if (structure.name.includes('پل')) {
                // پل را به صورت داینامیک بین start_kilometer و end_kilometer رسم کن
                const x1 = this.transformX(structure.start_kilometer);
                const x2 = this.transformX(structure.end_kilometer);
                // پیدا کردن y روی پروفیل جاده (نزدیک‌ترین نقطه به start_kilometer و end_kilometer)
                let y1 = null, y2 = null;
                if (profileData.road_points && profileData.road_points.length > 0) {
                    let minDist1 = Infinity, minDist2 = Infinity;
                    for (let p = 0; p < profileData.road_points.length; p++) {
                        const dist1 = Math.abs(profileData.road_points[p].x - structure.start_kilometer);
                        if (dist1 < minDist1) { minDist1 = dist1; y1 = this.transformY(profileData.road_points[p].y); }
                        const dist2 = Math.abs(profileData.road_points[p].x - structure.end_kilometer);
                        if (dist2 < minDist2) { minDist2 = dist2; y2 = this.transformY(profileData.road_points[p].y); }
                    }
                }
                if (y1 === null) y1 = this.transformY(profileData.road_points[0].y);
                if (y2 === null) y2 = this.transformY(profileData.road_points[profileData.road_points.length - 1].y);
                const yBridge = Math.min(y1, y2) - 30; // پل کمی بالاتر از پروفیل جاده
                const bridgeHeight = 18;
                const archHeight = 14;
                const pierWidth = 7;
                const ctx = this.canvas.ctx;
                ctx.save();
                // سایه و افکت وضعیت
                if (structure.status === 2) { ctx.shadowColor = '#7ed957'; ctx.shadowBlur = 16; }
                else if (structure.status === 1) { ctx.shadowColor = '#ffc107'; ctx.shadowBlur = 10; }
                else { ctx.shadowBlur = 0; }
                // بدنه پل (مستطیل)
                ctx.beginPath();
                ctx.rect(x1, yBridge, x2 - x1, bridgeHeight);
                ctx.fillStyle = '#90a4ae';
                ctx.globalAlpha = 0.92;
                ctx.fill();
                ctx.globalAlpha = 1;
                ctx.lineWidth = 2.2;
                ctx.strokeStyle = '#37474f';
                ctx.stroke();
                // قوس پل
                ctx.beginPath();
                ctx.moveTo(x1, yBridge + bridgeHeight);
                ctx.quadraticCurveTo((x1 + x2) / 2, yBridge + bridgeHeight + archHeight, x2, yBridge + bridgeHeight);
                ctx.lineWidth = 2.5;
                ctx.strokeStyle = '#607d8b';
                ctx.stroke();
                // پایه‌های پل
                ctx.beginPath();
                ctx.rect(x1 - pierWidth / 2, yBridge + bridgeHeight, pierWidth, 22);
                ctx.rect(x2 - pierWidth / 2, yBridge + bridgeHeight, pierWidth, 22);
                ctx.fillStyle = '#78909c';
                ctx.globalAlpha = 0.85;
                ctx.fill();
                ctx.globalAlpha = 1;
                ctx.strokeStyle = '#37474f';
                ctx.lineWidth = 1.5;
                ctx.stroke();
                // نام پل بالای قوس
                ctx.font = 'bold 13px Tahoma';
                ctx.fillStyle = '#263238';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.shadowColor = '#fff';
                ctx.shadowBlur = 6;
                ctx.fillText(structure.name, (x1 + x2) / 2, yBridge - 4);
                ctx.shadowBlur = 0;
                ctx.restore();
                // Add tooltipData for bridge (center)
                if (!this.tooltipData) this.tooltipData = [];
                this.tooltipData.push({
                    x: (x1 + x2) / 2,
                    y: yBridge + bridgeHeight / 2,
                    width: Math.abs(x2 - x1),
                    height: bridgeHeight + archHeight,
                    data: { type: 'bridge', structure }
                });
            } else {
                // سایر ابنیه‌ها (آبرو، تونل و ...)
                const x = this.transformX(structure.kilometer_location);
                const y = this.height / 2;
                this.drawStructureSymbol(structure, x, y);
            }
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
        const profileData = this.projectData.profile_data;
        if (!profileData.road_points || profileData.road_points.length === 0) return;
        
        const layers = this.projectData.layers;
        this.projectData.layers.forEach(layer => {
            layer.experiments.forEach(experiment => {
                if (this.isExperimentInDateRange(experiment)) {
                    const x = this.transformX(experiment.kilometer_start);
                    
                    // پیدا کردن موقعیت دقیق Y برای آزمایش - استفاده از executed_ranges
                    let yLayer = null;
                    
                    // اگر لایه executed_ranges دارد، از آن استفاده کن
                    if (layer.executed_ranges && Array.isArray(layer.executed_ranges) && layer.executed_ranges.length > 0) {
                        // پیدا کردن بازه‌ای که آزمایش در آن قرار دارد
                        for (const range of layer.executed_ranges) {
                            if (experiment.kilometer_start >= range.start && experiment.kilometer_start <= range.end) {
                                // interpolate برای موقعیت دقیق Y
                                let yRoad = null;
                                for (let p = 0; p < profileData.road_points.length - 1; p++) {
                                    const p1 = profileData.road_points[p];
                                    const p2 = profileData.road_points[p + 1];
                                    if (experiment.kilometer_start >= p1.x && experiment.kilometer_start <= p2.x) {
                                        const t = (experiment.kilometer_start - p1.x) / (p2.x - p1.x);
                                        yRoad = p1.y + (p2.y - p1.y) * t;
                                        break;
                                    }
                                }
                                if (yRoad === null) {
                                    let minDist = Infinity;
                                    for (let p = 0; p < profileData.road_points.length; p++) {
                                        const point = profileData.road_points[p];
                                        const dist = Math.abs(point.x - experiment.kilometer_start);
                                        if (dist < minDist) {
                                            minDist = dist;
                                            yRoad = point.y;
                                        }
                                    }
                                }
                                
                                // محاسبه موقعیت Y لایه بر اساس order_from_top
                                yLayer = this.transformY(yRoad);
                                const canvasHeight = this.height - this.margin * 2 - 30;
                                const maxLayerThicknessPx = canvasHeight * 0.12;
                                const minLayerThicknessPx = 2;
                                
                                // جمع کردن ضخامت لایه‌های قبلی
                                for (let l = 0; l < layers.length; l++) {
                                    const tempLayer = layers[l];
                                    if (tempLayer.order_from_top < layer.order_from_top) {
                                        let tempThickness = Math.max(Math.min(tempLayer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                                        if (tempLayer.state !== 1) {
                                            tempThickness = Math.max(tempThickness * 0.25, 1);
                                        }
                                        yLayer += tempThickness;
                                    } else if (tempLayer.order_from_top === layer.order_from_top) {
                                        // اضافه کردن نصف ضخامت لایه فعلی برای قرار دادن آزمایش در وسط لایه
                                        let tempThickness = Math.max(Math.min(tempLayer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                                        if (tempLayer.state !== 1) {
                                            tempThickness = Math.max(tempThickness * 0.25, 1);
                                        }
                                        yLayer += tempThickness / 2;
                                        break;
                                    }
                                }
                                break;
                            }
                        }
                    }
                    
                    // اگر executed_ranges نداشت یا آزمایش در هیچ بازه‌ای نبود، از روش قبلی استفاده کن
                    if (yLayer === null) {
                        let yRoad = null;
                        for (let p = 0; p < profileData.road_points.length - 1; p++) {
                            const p1 = profileData.road_points[p];
                            const p2 = profileData.road_points[p + 1];
                            if (experiment.kilometer_start >= p1.x && experiment.kilometer_start <= p2.x) {
                                const t = (experiment.kilometer_start - p1.x) / (p2.x - p1.x);
                                yRoad = p1.y + (p2.y - p1.y) * t;
                                break;
                            }
                        }
                        if (yRoad === null) {
                            let minDist = Infinity;
                            for (let p = 0; p < profileData.road_points.length; p++) {
                                const point = profileData.road_points[p];
                                const dist = Math.abs(point.x - experiment.kilometer_start);
                                if (dist < minDist) {
                                    minDist = dist;
                                    yRoad = point.y;
                                }
                            }
                        }
                        
                        yLayer = this.transformY(yRoad);
                        const canvasHeight = this.height - this.margin * 2 - 30;
                        const maxLayerThicknessPx = canvasHeight * 0.12;
                        const minLayerThicknessPx = 2;
                        
                        for (let l = 0; l < layers.length; l++) {
                            const tempLayer = layers[l];
                            if (tempLayer.order_from_top < layer.order_from_top) {
                                let tempThickness = Math.max(Math.min(tempLayer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                                if (tempLayer.state !== 1) {
                                    tempThickness = Math.max(tempThickness * 0.25, 1);
                                }
                                yLayer += tempThickness;
                            } else if (tempLayer.order_from_top === layer.order_from_top) {
                                let tempThickness = Math.max(Math.min(tempLayer.thickness_cm * this.yScale / 100, maxLayerThicknessPx), minLayerThicknessPx);
                                if (tempLayer.state !== 1) {
                                    tempThickness = Math.max(tempThickness * 0.25, 1);
                                }
                                yLayer += tempThickness / 2;
                                break;
                            }
                        }
                    }
                    
                    if (yLayer !== null) {
                        this.drawExperimentPixel(experiment, x, yLayer, layer);
                    }
                }
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
        // تبدیل مختصات X از کیلومتر به پیکسل
        // اضافه کردن margin برای فاصله از لبه چپ
        return this.margin + (x - this.xMin) * this.xScale;
    }

    transformY(y) {
        return this.margin + (this.yMax - y) * this.yScale;
    }

    handleMouseMove(e) {
        const canvas = document.getElementById('mainCanvas');
        const rect = canvas.getBoundingClientRect();
        
        // محاسبه ساده و مستقیم موقعیت موس
        // canvas.style.width/height همان اندازه logical است
        // mouseX و mouseY باید در واحدهای logical باشند
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;
        
        // اطمینان از اینکه موس در محدوده canvas است
        const canvasLogicalWidth = this.dynamicWidth || this.width;
        const canvasLogicalHeight = this.height;
        if (this.mouseX < 0 || this.mouseX > canvasLogicalWidth || this.mouseY < 0 || this.mouseY > canvasLogicalHeight) {
            this.mouseX = null;
            this.mouseY = null;
            this.render();
            return;
        }
        
        // بروزرسانی نمایش مختصات
        const realX = this.xMin + (this.mouseX - this.margin) / this.xScale;
        const realY = this.yMax - (this.mouseY - this.margin) / this.yScale;
        if (document.getElementById('xinput')) {
            document.getElementById('xinput').value = realX.toFixed(3);
        }
        if (document.getElementById('yinput')) {
            document.getElementById('yinput').value = realY.toFixed(3);
        }
        
        // render برای نمایش crosshair
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
            let html = '';
            const d = hoveredItem.data;
            if (d.type === 'layer') {
                const layer = d.layer;
                const statusMap = {0:'شروع نشده',1:'در حال انجام',2:'تکمیل شده'};
                const stateMap = {0:'متغیر',1:'ثابت'};
                let statusColor = layer.status === 2 ? '#7ed957' : layer.status === 1 ? '#ffc107' : '#bdbdbd';
                let icon = layer.status === 2 ? '✔' : layer.status === 1 ? '⏳' : '⏺';
                html = `<div style="display:flex;align-items:center;gap:6px;font-weight:bold;"><span style="font-size:18px;color:${statusColor}">${icon}</span> <span>${layer.name}</span></div>`;
                html += `<div style="font-size:12px;color:#555;">وضعیت: <b style='color:${statusColor}'>${statusMap[layer.status]}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">نوع: <b>${stateMap[layer.state]}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">ضخامت: <b>${layer.thickness_cm}cm</b></div>`;
                html += `<div style="font-size:12px;color:#555;">تعداد آزمایش: <b>${layer.experiments?.length||0}</b></div>`;
            } else if (d.type === 'bridge') {
                const s = d.structure;
                const statusMap = {0:'شروع نشده',1:'در حال انجام',2:'تکمیل شده'};
                let statusColor = s.status === 2 ? '#7ed957' : s.status === 1 ? '#ffc107' : '#bdbdbd';
                html = `<div style="display:flex;align-items:center;gap:6px;font-weight:bold;"><span style="font-size:18px;color:${statusColor}">🌉</span> <span>${s.name}</span></div>`;
                html += `<div style="font-size:12px;color:#555;">وضعیت: <b style='color:${statusColor}'>${statusMap[s.status]}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">کیلومتر شروع: <b>${s.start_kilometer}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">کیلومتر پایان: <b>${s.end_kilometer}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">طول پل: <b>${(s.end_kilometer-s.start_kilometer).toFixed(2)} km</b></div>`;
            } else if (d.experiment && d.layer) {
                // آزمایش
                const experiment = d.experiment;
                const layer = d.layer;
                const statusColors = {0:'#ffc107',1:'#17a2b8',2:'#28a745',3:'#dc3545'};
                const statusMap = {0:'در انتظار',1:'در حال انجام',2:'تکمیل شده',3:'رد شده'};
                html = `<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:18px;">🧪</span><span style="font-weight:bold;color:${statusColors[experiment.status]}">آزمایش ${experiment.experiment_type}</span></div>`;
                html += `<div style="font-size:13px;color:#555;">لایه: <b>${layer.name}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">کیلومتر: <b>${experiment.kilometer_start} - ${experiment.kilometer_end}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">تاریخ: <b>${experiment.request_date || 'نامشخص'}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">وضعیت: <b>${statusMap[experiment.status]}</b></div>`;
                if (experiment.description) html += `<div style='font-size:12px;color:#888;margin-top:2px;'>${experiment.description}</div>`;
            }
            tooltip.innerHTML = html;
            tooltip.style.display = 'block';
            // --- موقعیت‌دهی دقیق تولتیپ زیر موس و زیر علامت + ---
            const canvas = document.getElementById('mainCanvas');
            const rect = canvas.getBoundingClientRect();
            const pageX = rect.left + hoveredItem.x + window.scrollX;
            const pageY = rect.top + hoveredItem.y + window.scrollY;
            // تولتیپ را دقیقاً زیر نقطه hover و علامت + قرار بده
            tooltip.style.left = (pageX - tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = (pageY + 16) + 'px'; // 16px پایین‌تر از مرکز علامت +
            tooltip.style.background = 'rgba(255,255,255,0.7)';
            tooltip.style.backdropFilter = 'blur(8px)';
            tooltip.style.borderRadius = '8px';
            tooltip.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
            tooltip.style.color = '#222';
            tooltip.style.padding = '10px 14px';
            tooltip.style.fontSize = '13px';
            tooltip.style.pointerEvents = 'none';
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
        // غیرفعال
        return;
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
        // افزایش سطح زوم
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 5.0); // حداکثر 5 برابر
        this.calculateScales();
        this.render();
    }

    zoomOut() {
        // کاهش سطح زوم
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 1.0); // حداقل 1 برابر (بدون زوم)
        this.calculateScales();
        this.render();
    }

    resetZoom() {
        // بازنشانی زوم به حالت اولیه
        this.zoomLevel = 1.0;
        this.zoomCenterX = null;
        this.zoomCenterY = null;
        this.calculateScales();
        this.render();
    }

    drawCrosshair(x, y) {
        const ctx = this.canvas.ctx;
        ctx.save();
        // نشانگر ساده و دقیق - فقط علامت + در مرکز
        const canvasWidth = this.dynamicWidth || this.width;
        
        // خطوط راهنما (کمرنگ)
        ctx.strokeStyle = 'rgba(44,62,80,0.2)';
        ctx.lineWidth = 1;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, this.height);
        ctx.moveTo(0, y);
        ctx.lineTo(canvasWidth, y);
        ctx.stroke();
        
        // علامت + ساده در مرکز
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(x - 6, y);
        ctx.lineTo(x + 6, y);
        ctx.moveTo(x, y - 6);
        ctx.lineTo(x, y + 6);
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

            // هاشور مورب با زاویه ۴۵ درجه - بهبود کیفیت و وضوح
            let color = 'rgba(200,200,200,0.3)';
            if (isExcavation) color = 'rgba(255,0,0,0.75)'; // قرمز پررنگ‌تر برای خاکبرداری
            if (isEmbankment) color = 'rgba(0,100,255,0.65)'; // آبی پررنگ‌تر برای خاکریزی
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.8; // ضخامت مناسب برای وضوح
            ctx.lineCap = 'round';
            // خطوط مورب ۴۵ درجه با فاصله مناسب
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            const minY = Math.min(yLand1, yRoad1, yLand2, yRoad2);
            const maxY = Math.max(yLand1, yRoad1, yLand2, yRoad2);
            const spacing = 6; // فاصله مناسب برای وضوح بهتر مناطق
            for (let d = minX - (maxY - minY); d < maxX + (maxY - minY); d += spacing) {
                ctx.beginPath();
                ctx.moveTo(d, minY - 20);
                ctx.lineTo(d + (maxY - minY) + 40, maxY + 20);
                ctx.stroke();
            }
            ctx.restore();
        }
        ctx.restore();
    }

    applyDateFilter() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        this.dateFilterStart = startDate ? new Date(startDate) : null;
        this.dateFilterEnd = endDate ? new Date(endDate) : null;
        
        // اعتبارسنجی تاریخ‌ها
        if (this.dateFilterStart && this.dateFilterEnd && this.dateFilterStart > this.dateFilterEnd) {
            alert('تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد!');
            return;
        }
        
        this.render();
        this.updateFilterStatus();
    }
    
    clearDateFilter() {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        this.dateFilterStart = null;
        this.dateFilterEnd = null;
        this.render();
        this.updateFilterStatus();
    }
    
    updateFilterStatus() {
        const applyBtn = document.getElementById('applyDateFilter');
        const clearBtn = document.getElementById('clearDateFilter');
        
        if (this.dateFilterStart || this.dateFilterEnd) {
            applyBtn.classList.remove('btn-primary');
            applyBtn.classList.add('btn-success');
            applyBtn.innerHTML = '<i class="fas fa-check"></i> فیلتر فعال';
            clearBtn.style.display = 'inline-block';
        } else {
            applyBtn.classList.remove('btn-success');
            applyBtn.classList.add('btn-primary');
            applyBtn.innerHTML = '<i class="fas fa-filter"></i> اعمال فیلتر';
            clearBtn.style.display = 'inline-block';
        }
    }
    
    isExperimentInDateRange(experiment) {
        if (!this.dateFilterStart && !this.dateFilterEnd) {
            return true; // بدون فیلتر
        }
        
        if (!experiment.request_date) {
            return false; // آزمایش بدون تاریخ
        }
        
        const experimentDate = new Date(experiment.request_date);
        
        if (this.dateFilterStart && experimentDate < this.dateFilterStart) {
            return false;
        }
        
        if (this.dateFilterEnd && experimentDate > this.dateFilterEnd) {
            return false;
        }
        
        return true;
    }
} 