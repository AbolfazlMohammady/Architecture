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
        this.layerLayout = null;
        this.layerIndexMap = new Map();
        this.hoveredTooltipItem = null;
        
        // فلگ برای جلوگیری از محاسبه مجدد مقیاس‌ها
        this._scalesCalculated = false;
        
        // فلگ برای بهینه‌سازی render در handleMouseMove
        this._renderRequested = false;
        
        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupEventListeners();
        // محاسبه مقیاس‌ها یک بار قبل از render
        this.calculateScales();
        this.render();
        // نمایش اطلاعات در کنسول
        this.logChartInfo();
    }
    
    logChartInfo() {
        console.group('📊 اطلاعات نمودار داشبورد');
        const profileData = this.projectData.profile_data;
        
        // محاسبه محدوده X از داده‌های پروفیل
        let xMinFromProfile = null;
        let xMaxFromProfile = null;
        if (profileData && profileData.land_points && profileData.land_points.length > 0) {
            const xValues = profileData.land_points
                .map(p => p && p.x !== undefined && p.x !== null && isFinite(p.x) ? p.x : null)
                .filter(x => x !== null);
            if (xValues.length > 0) {
                xMinFromProfile = Math.min(...xValues);
                xMaxFromProfile = Math.max(...xValues);
            }
        }
        
        // محاسبه محدوده Y از داده‌های پروفیل
        let yMinFromProfile = null;
        let yMaxFromProfile = null;
        if (profileData && profileData.land_points && profileData.land_points.length > 0) {
            const yValues = profileData.land_points
                .map(p => p && p.y !== undefined && p.y !== null && isFinite(p.y) ? p.y : null)
                .filter(y => y !== null);
            if (yValues.length > 0) {
                yMinFromProfile = Math.min(...yValues);
                yMaxFromProfile = Math.max(...yValues);
            }
        }
        
        console.log('محدوده X (از پروفیل):', {
            min: xMinFromProfile,
            max: xMaxFromProfile,
            range: xMaxFromProfile && xMinFromProfile ? xMaxFromProfile - xMinFromProfile : null
        });
        console.log('محدوده Y (از پروفیل):', {
            min: yMinFromProfile,
            max: yMaxFromProfile,
            range: yMaxFromProfile && yMinFromProfile ? yMaxFromProfile - yMinFromProfile : null
        });
        console.log('محدوده X (محاسبه شده از پروفیل):', {
            min: this.originalXMin,
            max: this.originalXMax,
            range: this.originalXMax && this.originalXMin ? this.originalXMax - this.originalXMin : null
        });
        console.log('محدوده Y (محاسبه شده):', {
            min: this.originalYMin || this.yMin,
            max: this.originalYMax || this.yMax,
            range: (this.originalYMax || this.yMax) - (this.originalYMin || this.yMin)
        });
        console.log('مقیاس‌ها:', {
            xScale: this.xScale,
            yScale: this.yScale,
            dynamicWidth: this.dynamicWidth
        });
        console.log('لایه‌ها:', this.projectData.layers?.map(l => ({
            name: l.name,
            experiments: l.experiments?.length || 0,
            executed_ranges: l.executed_ranges?.length || 0
        })));
        console.log('آزمایش‌ها (از داده‌های واقعی):', this.projectData.layers?.flatMap(l => 
            (l.experiments || []).map(e => ({
                id: e.id,
                kilometer_start: e.kilometer_start,
                kilometer_end: e.kilometer_end,
                status: e.status,
                layer: l.name
            }))
        ) || []);
        console.log('نقاط پروفیل:', {
            land_points: this.projectData.profile_data?.land_points?.length || 0,
            road_points: this.projectData.profile_data?.road_points?.length || 0,
            first_land_point: this.projectData.profile_data?.land_points?.[0],
            last_land_point: this.projectData.profile_data?.land_points?.[this.projectData.profile_data?.land_points?.length - 1]
        });
        console.groupEnd();
    }

    setupCanvas() {
        // Calculate dynamic width based on actual data range (including experiments)
        // ابتدا محدوده واقعی را از داده‌های پروفیل محاسبه می‌کنیم
        const profileData = this.projectData.profile_data;
        let actualXMin = null;
        let actualXMax = null;
        
        // محاسبه محدوده X از داده‌های پروفیل
        if (profileData && profileData.land_points && profileData.land_points.length > 0) {
            const xValues = profileData.land_points
                .map(p => p && p.x !== undefined && p.x !== null && isFinite(p.x) ? p.x : null)
                .filter(x => x !== null);
            if (xValues.length > 0) {
                actualXMin = Math.min(...xValues);
                actualXMax = Math.max(...xValues);
            }
        }
        
        // اگر از پروفیل چیزی پیدا نشد، خطا نمایش می‌دهیم (نه هاردکد)
        if (actualXMin === null || actualXMax === null) {
            console.warn('محدوده X از پروفیل محاسبه نشده است. استفاده از مقادیر پیش‌فرض.');
            actualXMin = 0;
            actualXMax = 10;
        }
        
        // محدوده X باید فقط از پروفیل خوانده شود، نه از آزمایش‌ها
        // آزمایش‌ها فقط برای نمایش استفاده می‌شوند و نباید در محاسبه محدوده X استفاده شوند
        
        const actualLength = actualXMax - actualXMin;
        const pxPerKm = 180; // زوم اولیه بیشتر برای وضوح لایه‌ها
        const minWidth = 1600;
        const baseDrawingWidth = Math.max(minWidth, Math.ceil(actualLength * pxPerKm));
        this.drawingWidth = baseDrawingWidth;
        
        // padding اضافی برای حاشیه‌های چپ/راست و کمی فضای باز در انتهای نمودار
        this.extraScrollPadding = Math.max(this.margin, 200);
        this.dynamicWidth = this.drawingWidth + this.margin * 2;
        
        // Set the inner div width to match canvas for full scroll
        const chartInner = document.getElementById('chart-canvas-inner');
        if (chartInner) {
            // عرض دقیق - نه 100%
            const innerWidth = this.dynamicWidth + this.extraScrollPadding;
            chartInner.style.width = innerWidth + 'px';
            chartInner.style.minWidth = innerWidth + 'px';
            chartInner.style.maxWidth = innerWidth + 'px';
            chartInner.style.paddingRight = this.extraScrollPadding + 'px';
            chartInner.style.display = 'block';
            chartInner.style.position = 'relative';
        }
        this.chartScrollContainer = document.getElementById('chart-scroll-x');
        if (this.chartScrollContainer) {
            // فعال کردن اسکرول افقی - با !important
            this.chartScrollContainer.style.setProperty('overflow-x', 'auto', 'important');
            this.chartScrollContainer.style.setProperty('overflow-y', 'hidden', 'important');
            this.chartScrollContainer.style.width = '100%';
            this.chartScrollContainer.style.height = '100%';
            this.chartScrollContainer.scrollLeft = 0;
            this.chartScrollContainer.scrollTop = 0;
            // اطمینان از اینکه اسکرول کار می‌کند
            console.log('Chart scroll container width:', this.chartScrollContainer.offsetWidth);
            console.log('Chart inner container width:', chartInner ? chartInner.offsetWidth : 'N/A');
            console.log('Dynamic width:', this.dynamicWidth);
        }
        
        // ایجاد canvas اصلی - باید قبل از تنظیم style باشد
        // استفاده از actualXMin و actualXMax از پروفیل (نه از projectData)
        this.canvas = new Canvas({
            containerId: this.containerId,
            width: this.dynamicWidth,
            height: this.height,
            margin: this.margin,
            start_kilometer: actualXMin || 0,
            end_kilometer: actualXMax || 10
        });
        
        // تنظیم عرض canvas و محور X برای اسکرول - اطمینان از اینکه فشرده نمی‌شود
        // این تنظیمات باید بعد از ایجاد Canvas باشد تا canvas.js بتواند canvas را تنظیم کند
        const mainCanvas = document.getElementById('mainCanvas');
        if (mainCanvas) {
            mainCanvas.style.width = this.dynamicWidth + 'px';
            mainCanvas.style.minWidth = this.dynamicWidth + 'px';
            mainCanvas.style.maxWidth = this.dynamicWidth + 'px';
            mainCanvas.style.display = 'block';
            mainCanvas.style.flexShrink = '0';
            console.log('Main canvas width set to:', this.dynamicWidth);
        }
        const xAxisCanvas = document.getElementById('xAxisCanvas');
        if (xAxisCanvas) {
            const xAxisWidth = this.dynamicWidth;
            xAxisCanvas.style.width = xAxisWidth + 'px';
            xAxisCanvas.style.minWidth = xAxisWidth + 'px';
            xAxisCanvas.style.maxWidth = xAxisWidth + 'px';
            xAxisCanvas.style.display = 'block';
            xAxisCanvas.style.flexShrink = '0';
            console.log('X axis canvas width set to:', xAxisWidth);
        }

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
            width: this.dynamicWidth,
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

        const scrollContainer = document.getElementById('chart-scroll-x');
        if (scrollContainer) {
            scrollContainer.addEventListener('wheel', (e) => {
                if (!e.shiftKey && Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                    scrollContainer.scrollLeft += e.deltaY;
                    e.preventDefault();
                }
            }, { passive: false });
        }
    }

    render() {
        // لاگ برای دیباگ - بررسی تغییر مقیاس‌ها
        const beforeXScale = this.xScale;
        const beforeYScale = this.yScale;
        
        // اطمینان از اینکه مقیاس‌ها محاسبه شده‌اند
        if (!this._scalesCalculated) {
            this.calculateScales();
        }
        
        this.canvas.clear();
        this.profileTooltipData = [];
        this.tooltipData = [];
        this.layerLayout = null;
        this.layerIndexMap = new Map();
        this.hoveredTooltipItem = null;
        
        // محاسبه مقیاس‌ها را از render حذف کردیم
        // مقیاس‌ها فقط یک بار در init() محاسبه می‌شوند
        // این باعث می‌شود که مقیاس‌ها ثابت بمانند و زوم خودکار نداشته باشیم
        
        // بررسی تغییر مقیاس‌ها بعد از drawAxes
        this.drawAxes();
        this.drawZeroAxisLine();
        
        // لاگ برای دیباگ - بررسی تغییر مقیاس‌ها بعد از drawAxes
        if (beforeXScale !== undefined && beforeYScale !== undefined) {
            if (this.xScale !== beforeXScale || this.yScale !== beforeYScale) {
                console.warn('⚠️ مقیاس‌ها تغییر کردند!', {
                    before: { xScale: beforeXScale, yScale: beforeYScale },
                    after: { xScale: this.xScale, yScale: this.yScale },
                    dynamicWidth: this.dynamicWidth,
                    xMin: this.xMin,
                    xMax: this.xMax,
                    yMin: this.yMin,
                    yMax: this.yMax
                });
            }
        }
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
        this.drawTooltipMarkers();
        // crosshair را فقط اینجا بکش
        if (this.mouseX !== null && this.mouseY !== null) {
            this.drawCrosshair(this.mouseX, this.mouseY);
            this.showProfileTooltip(this.mouseX, this.mouseY);
            this.showTooltip(this.mouseX, this.mouseY);
        }
    }

    calculateScales() {
        // اگر مقیاس‌ها قبلاً محاسبه شده‌اند، دوباره محاسبه نکن
        if (this._scalesCalculated) {
            return;
        }
        
        const profileData = this.projectData.profile_data;
        if (!profileData.land_points || profileData.land_points.length === 0) {
            console.error('هیچ داده‌ای از پروفیل وجود ندارد!');
            return;
        }

        // محاسبه محدوده X مستقیماً از داده‌های پروفیل
        const xValues = [];
        if (profileData.land_points && profileData.land_points.length > 0) {
            profileData.land_points.forEach(p => {
                if (p && p.x !== undefined && p.x !== null && isFinite(p.x)) {
                    xValues.push(p.x);
                }
            });
        }
        if (profileData.road_points && profileData.road_points.length > 0) {
            profileData.road_points.forEach(p => {
                if (p && p.x !== undefined && p.x !== null && isFinite(p.x)) {
                    xValues.push(p.x);
                }
            });
        }
        
        if (xValues.length === 0) {
            console.error('هیچ داده X از پروفیل وجود ندارد!');
            this.originalXMin = 0;
            this.originalXMax = 10;
        } else {
            this.originalXMin = Math.min(...xValues);
            this.originalXMax = Math.max(...xValues);
        }
        
        // محاسبه محدوده Y مستقیماً از داده‌های پروفیل
        const yValues = profileData.land_points
            .map(p => p.y)
            .filter(y => y !== null && y !== undefined && isFinite(y));
        
        if (yValues.length === 0) {
            console.error('هیچ داده Y از پروفیل وجود ندارد!');
            this.originalYMin = -10;
            this.originalYMax = 10;
        } else {
            let yMinFromData = Math.min(...yValues);
            let yMaxFromData = Math.max(...yValues);
            
            // اطمینان از اینکه صفر در محدوده است
            if (yMinFromData > 0) {
                yMinFromData = 0;
            } else if (yMaxFromData < 0) {
                yMaxFromData = 0;
            }
            
            // اضافه کردن margin کوچک (5% از هر طرف)
            const yRange = yMaxFromData - yMinFromData;
            const yMargin = Math.max(yRange * 0.05, 0.5);
            this.originalYMin = yMinFromData - yMargin;
            this.originalYMax = yMaxFromData + yMargin;
        }

        // تنظیم محدوده‌های نهایی
        this.xMin = this.originalXMin;
        this.xMax = this.originalXMax;
        
        // برای محور Y، باید مطمئن شویم که صفر دقیقاً در مرکز محدوده است
        // یا حداقل در محدوده باشد
        this.yMin = this.originalYMin;
        this.yMax = this.originalYMax;
        
        // اطمینان از اینکه صفر در محدوده Y است
        if (this.yMin > 0) {
            this.yMin = 0;
        } else if (this.yMax < 0) {
            this.yMax = 0;
        }
        
        // اطمینان از اینکه محدوده Y متقارن حول صفر است (یا حداقل صفر در آن است)
        // این باعث می‌شود که transformY(0) دقیقاً روی خط 0.0 محور Y قرار بگیرد
        if (this.yMin < 0 && this.yMax > 0) {
            // اگر هر دو طرف صفر وجود دارد، محدوده را متقارن کنیم
            const maxAbs = Math.max(Math.abs(this.yMin), Math.abs(this.yMax));
            this.yMin = -maxAbs;
            this.yMax = maxAbs;
        }
        
        // اطمینان از اعتبار محدوده‌ها
        if (this.xMin >= this.xMax) {
            console.error('محدوده X نامعتبر است!', { xMin: this.xMin, xMax: this.xMax });
            this.xMin = 0;
            this.xMax = 10;
        }
        if (this.yMin >= this.yMax) {
            console.error('محدوده Y نامعتبر است!', { yMin: this.yMin, yMax: this.yMax });
            this.yMin = -10;
            this.yMax = 10;
        }
        
        // محاسبه مقیاس‌ها
        const effectiveDrawingWidth = this.drawingWidth || ((this.dynamicWidth || this.width) - this.margin * 2);
        const canvasHeight = this.height - this.margin * 2 - 30;
        
        const xRange = this.xMax - this.xMin;
        const yRange = this.yMax - this.yMin;
        
        this.xScale = effectiveDrawingWidth / xRange;
        this.yScale = canvasHeight / yRange;
        
        // لاگ برای دیباگ
        console.log('✅ مقیاس‌ها از پروفیل محاسبه شدند:', {
            xMin: this.xMin,
            xMax: this.xMax,
            yMin: this.yMin,
            yMax: this.yMax,
            xScale: this.xScale,
            yScale: this.yScale,
            transformY0: this.transformY(0),
            canvasWidth: effectiveDrawingWidth,
            canvasHeight: canvasHeight
        });
        
        // علامت‌گذاری که مقیاس‌ها محاسبه شده‌اند
        this._scalesCalculated = true;
    }

    drawAxes() {
        // اطمینان از اینکه مقیاس‌ها محاسبه شده‌اند
        if (!this._scalesCalculated) {
            this.calculateScales();
        }
        
        // بروزرسانی محور X - مستقیماً از this.xMin و this.xMax
        const xLabels = [];
        if (!this.xMin || !this.xMax) {
            console.warn('محدوده X محاسبه نشده است. لطفاً پروفیل را بررسی کنید.');
            return;
        }
        const start = this.xMin; // مستقیماً از this.xMin
        const end = this.xMax; // مستقیماً از this.xMax
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
        this.xAxis.update(xLabels, start, end, this.xScale, this.xMin);
        
        // بروزرسانی محور Y - مستقیماً از this.yMin و this.yMax
        const yLabels = [];
        // استفاده مستقیم از this.yMin و this.yMax
        const dataYMin = this.yMin;
        const dataYMax = this.yMax;
        const yRange = dataYMax - dataYMin;
        
        // محاسبه step داینامیک بر اساس محدوده Y (از پروفیل)
        let yStep;
        if (yRange <= 5) {
            yStep = 0.5; // برای محدوده کوچک، step 0.5
        } else if (yRange <= 10) {
            yStep = 1; // برای محدوده متوسط، step 1
        } else if (yRange <= 20) {
            yStep = 2; // برای محدوده بزرگتر، step 2
        } else if (yRange <= 50) {
            yStep = 5; // برای محدوده خیلی بزرگ، step 5
        } else {
            yStep = 10; // برای محدوده خیلی خیلی بزرگ， step 10
        }
        
        // گرد کردن به مضرب‌های step برای نمایش بهتر (اما بر اساس داده‌های پروفیل)
        // اطمینان از اینکه صفر در لیبل‌ها باشد
        let yMinRounded = Math.floor(dataYMin / yStep) * yStep;
        let yMaxRounded = Math.ceil(dataYMax / yStep) * yStep;
        
        // اطمینان از اینکه صفر در محدوده باشد
        if (yMinRounded > 0) {
            yMinRounded = 0;
        } else if (yMaxRounded < 0) {
            yMaxRounded = 0;
        }
        
        // محدوده Y را بر اساس داده‌های واقعی پروفیل تنظیم می‌کنیم (با step داینامیک)
        const finalYMin = yMinRounded;
        const finalYMax = yMaxRounded;
        
        // اطمینان از اینکه yMin و yMax در dashboard با yAxis یکسان هستند
        // این مهم است چون transformY از this.yMin و this.yMax استفاده می‌کند
        this.yMin = finalYMin;
        this.yMax = finalYMax;
        
        // محاسبه مجدد yScale بر اساس finalYMin و finalYMax
        const mainCanvasHeight = this.height - this.margin * 2 - 30;
        const currentYRange = this.yMax - this.yMin;
        if (currentYRange > 0) {
            this.yScale = mainCanvasHeight / currentYRange;
        }
        
        // ایجاد لیبل‌ها با فرمت عددی (بدون "m" برای سازگاری با yaxiscanvas)
        for (let value = finalYMin; value <= finalYMax + 0.0001; value += yStep) {
            yLabels.push(value.toFixed(1));
        }

        // اطمینان از اینکه مقدار صفر همیشه در لیست لیبل‌ها وجود دارد
        if (this.yMin < 0 && this.yMax > 0) {
            const hasZero = yLabels.some(label => Math.abs(parseFloat(label)) < 1e-6);
            if (!hasZero) {
                yLabels.push('0.0');
                yLabels.sort((a, b) => parseFloat(a) - parseFloat(b));
            }
        }
        
        // استفاده از finalYMin و finalYMax برای yAxis.update
        // این باعث می‌شود که لیبل‌های Y دقیقاً از داده‌های پروفیل خوانده شوند
        this.yAxis.update(yLabels, finalYMin, finalYMax);

        const yMain0 = this.transformY(0);
        const debugAxisZero = (typeof this.yAxis.getYPosition === 'function') ? this.yAxis.getYPosition(0) : null;
        const debugDiff = (typeof debugAxisZero === 'number') ? (yMain0 - debugAxisZero) : null;

        const mainCanvasEl = this.canvas && this.canvas.canvas ? this.canvas.canvas : null;
        const yAxisCanvasEl = this.yAxis && this.yAxis.canvas ? this.yAxis.canvas : null;
        let screenDiff = null;
        if (mainCanvasEl && yAxisCanvasEl && typeof yMain0 === 'number' && typeof debugAxisZero === 'number') {
            const mainRect = mainCanvasEl.getBoundingClientRect();
            const axisRect = yAxisCanvasEl.getBoundingClientRect();
            const mainScreenY = mainRect.top + yMain0;
            const axisScreenY = axisRect.top + debugAxisZero;
            screenDiff = axisScreenY - mainScreenY;
        }

        const shouldFix = (typeof debugDiff === 'number' && Math.abs(debugDiff) > 0.5) ||
                          (screenDiff !== null && Math.abs(screenDiff) > 0.5);
        if (shouldFix && screenDiff !== null) {
            const shift = Math.round(screenDiff * 100) / 100;
            if (yAxisCanvasEl) {
                yAxisCanvasEl.style.transform = `translateY(${shift}px)`;
            } else if (this.yAxis && this.yAxis.ctx && typeof this.yAxis.ctx.translate === 'function') {
                this.yAxis.ctx.save();
                this.yAxis.ctx.translate(0, shift);
                this.yAxis.ctx.restore();
            }
        } else if (yAxisCanvasEl && Math.abs(screenDiff || 0) <= 0.5) {
            yAxisCanvasEl.style.transform = '';
        }
        
        // بررسی اینکه transformY(0) دقیقاً روی خط 0.0 محور Y قرار می‌گیرد
        const transformY0 = this.transformY(0);
        const yAxis0 = this.yAxis.getYPosition(0); // موقعیت 0.0 در محور Y
        
        // بررسی هماهنگی بین transformY و yAxis
        const paddingY = 10;
        const yAxisCanvasHeightUsable = this.height - paddingY * 2;
        const normalizedY0 = (0 - this.yMin) / (this.yMax - this.yMin);
        
        // محاسبه موقعیت 0.0 در canvas اصلی - باید با transformY0 یکسان باشد
        const expectedY0 = this.margin + mainCanvasHeight - (normalizedY0 * mainCanvasHeight);
        
        const diff = Math.abs(transformY0 - expectedY0);
        if (diff > 0.1) {
            console.warn('⚠️ transformY و yAxis هماهنگ نیستند!', {
                transformY0: transformY0,
                expectedY0: expectedY0,
                yAxis0: yAxis0,
                margin: this.margin,
                mainCanvasHeight: mainCanvasHeight,
                yAxisCanvasHeightUsable: yAxisCanvasHeightUsable,
                normalizedY0: normalizedY0,
                diff: diff
            });
        }
        
        // لاگ برای دیباگ
        console.log('✅ محور Y تنظیم شد:', {
            finalYMin: finalYMin,
            finalYMax: finalYMax,
            yMin: this.yMin,
            yMax: this.yMax,
            yScale: this.yScale,
            transformY0: transformY0,
            expectedY0: expectedY0,
            yAxis0: yAxis0,
            margin: this.margin,
            mainCanvasHeight: mainCanvasHeight,
            yRange: currentYRange,
            diff: diff
        });
    }

    drawZeroAxisLine() {
        // تنها زمانی که صفر در محدوده Y قرار دارد، خط پایه را رسم کن
        if (!(this.yMin <= 0 && this.yMax >= 0)) {
            return;
        }
        const ctx = this.canvas.ctx;
        const yZero = this.transformY(0);
        ctx.save();
        ctx.strokeStyle = '#ff9800'; // رنگ واضح برای خط صفر
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        const startX = this.margin;
        const endX = (this.dynamicWidth || this.width) - this.margin;
        ctx.beginPath();
        ctx.moveTo(startX, yZero);
        ctx.lineTo(endX, yZero);
        ctx.stroke();
        ctx.restore();
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
        
        // بهبود کیفیت رندرینگ
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        
        // سایه ضخیم زیر پروفیل - بهبود کیفیت
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
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.shadowColor = 'rgba(56,249,215,0.25)';
        ctx.shadowBlur = 8;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.stroke();
        
        // خط اصلی پروفیل - کیفیت حرفه‌ای
        ctx.shadowBlur = 0;
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#43e97b');
        grad.addColorStop(0.5, '#3de8a8');
        grad.addColorStop(1, '#38f9d7');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.5; // کاهش ضخامت برای جلوگیری از پوشش خط صفر
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
        
        // اطمینان از اینکه transformY(0) درست کار می‌کند
        const yZero = this.transformY(0);
        console.log('رسم خط جاده - transformY(0):', yZero, {
            yMin: this.yMin,
            yMax: this.yMax,
            yScale: this.yScale,
            margin: this.margin
        });
        
        const points = profileData.road_points.map(point => ({
            x: this.transformX(point.x),
            y: yZero // همه نقاط جاده روی ارتفاع صفر - استفاده از مقدار محاسبه شده
        }));
        const ctx = this.canvas.ctx;
        ctx.save();
        // بهبود کیفیت رندرینگ
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        
        // گرادینت آبی-بنفش برای پروفیل جاده - کیفیت حرفه‌ای
        const grad = ctx.createLinearGradient(points[0].x, 0, points[points.length-1].x, 0);
        grad.addColorStop(0, '#00c6ff');
        grad.addColorStop(0.5, '#0099ff');
        grad.addColorStop(1, '#0072ff');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2.5; // کمی نازک‌تر برای تمایز بهتر با خط صفر
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.shadowColor = 'rgba(0,198,255,0.25)';
        ctx.shadowBlur = 3;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
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

    buildLayerLayout() {
        const layout = {
            layers: [],
            boundaries: [],
            centers: [],
            thicknessPx: []
        };

        const profileData = this.projectData.profile_data;
        if (!profileData || !profileData.road_points || profileData.road_points.length === 0) {
            this.layerIndexMap = new Map();
            return layout;
        }

        const sortedLayers = [...(this.projectData.layers || [])].sort(
            (a, b) => (a.order_from_top || 0) - (b.order_from_top || 0)
        );

        if (!sortedLayers.length) {
            this.layerIndexMap = new Map();
            return layout;
        }

                const canvasHeight = this.height - this.margin * 2 - 30;
        const maxLayerThicknessPx = canvasHeight * 0.14;
        const minLayerThicknessPx = 1.2;

        const desiredThicknessPx = sortedLayers.map(layer =>
            Math.max(
                Math.min((layer.thickness_cm || 0) * (this.yScale || 0) / 100, maxLayerThicknessPx),
                minLayerThicknessPx
            )
        );

        const cumulativeDesiredPx = desiredThicknessPx.reduce((acc, val) => acc + val, 0);

        const boundaries = Array.from({ length: sortedLayers.length + 1 }, () => []);
        const centers = Array.from({ length: sortedLayers.length }, () => []);
        const thicknessAccumulator = new Array(sortedLayers.length).fill(0);
        const thicknessSamples = new Array(sortedLayers.length).fill(0);

        const roadPoints = profileData.road_points;

        for (let i = 0; i < roadPoints.length; i++) {
            const point = roadPoints[i];
            const km = point.x;
            const x = this.transformX(km);
            const roadY = this.transformY(point.y);
            const landElevation = this.getLandElevationAt(km);
            const fallbackLandY = roadY + cumulativeDesiredPx + 40;
            const landY = Number.isFinite(landElevation)
                ? Math.max(this.transformY(landElevation), roadY)
                : fallbackLandY;
            const totalAvailable = Math.max(landY - roadY, 0);

            boundaries[0].push({ x, y: roadY, km, valid: true, index: i });

            let allocatedPx = 0;

            for (let l = 0; l < sortedLayers.length; l++) {
                const layer = sortedLayers[l];
                const desiredPx = desiredThicknessPx[l];
                const isFixed = layer.state === 1;

                let effectivePx = desiredPx;
                const remaining = Math.max(totalAvailable - allocatedPx, 0);

                if (!isFixed) {
                    effectivePx = Math.min(desiredPx, remaining);
                } else if (remaining < desiredPx && remaining > 0) {
                    effectivePx = Math.min(desiredPx, remaining);
                }

                if (!Number.isFinite(effectivePx) || effectivePx < 0) {
                    effectivePx = 0;
                }

                const bottomTarget = roadY + allocatedPx + effectivePx;
                const clampedBottom = Math.min(bottomTarget, landY);
                const actualThickness = Math.max(clampedBottom - (roadY + allocatedPx), 0);
                const hasThickness = isFixed ? desiredPx > 0 : actualThickness > 0.6;

                const bottomPoint = {
                    x,
                    y: roadY + allocatedPx + actualThickness,
                    km,
                    valid: isFixed || hasThickness,
                    index: i
                };
                boundaries[l + 1].push(bottomPoint);

                const centerPoint = {
                    x,
                    y: roadY + allocatedPx + actualThickness / 2,
                    km,
                    valid: hasThickness,
                    index: i
                };
                centers[l].push(centerPoint);

                if (actualThickness > 0) {
                    allocatedPx += actualThickness;
                    thicknessAccumulator[l] += actualThickness;
                    thicknessSamples[l] += 1;
                } else if (isFixed) {
                    allocatedPx += desiredPx;
                    thicknessAccumulator[l] += desiredPx;
                    thicknessSamples[l] += 1;
                }
            }
        }

        const thicknessPx = sortedLayers.map((layer, idx) => {
            if (thicknessSamples[idx] > 0) {
                return thicknessAccumulator[idx] / thicknessSamples[idx];
            }
            return desiredThicknessPx[idx];
        });

        this.layerIndexMap = new Map(sortedLayers.map((layer, index) => [layer.id, index]));

        layout.layers = sortedLayers;
        layout.boundaries = boundaries;
        layout.centers = centers;
        layout.thicknessPx = thicknessPx;
        return layout;
    }

    drawLayers() {
        const layout = this.buildLayerLayout();
        const ctx = this.canvas.ctx;
        const { layers, boundaries, centers, thicknessPx } = layout;
        if (!layers.length) {
            this.layerLayout = layout;
            return;
        }

        if (!this.tooltipData) {
            this.tooltipData = [];
        }

        for (let index = 0; index < layers.length; index++) {
            const layer = layers[index];
            const topBoundary = boundaries[index];
            const bottomBoundary = boundaries[index + 1];
            const centerLine = centers[index];
            const segments = this.extractConnectedSegments(topBoundary);
            if (!segments.length) {
                continue;
            }

            ctx.save();
            ctx.lineWidth = layer.state === 1 ? 1.15 : 1.6;
            ctx.strokeStyle = layer.state === 1 ? '#1f2937' : '#fb923c';
            ctx.setLineDash(layer.state === 1 ? [] : [5, 6]);
            ctx.globalAlpha = layer.state === 1 ? 0.9 : 1;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            segments.forEach(segment => {
                if (segment.length < 2) {
                    return;
                }
                ctx.beginPath();
                ctx.moveTo(segment[0].x, segment[0].y);
                for (let i = 1; i < segment.length; i++) {
                    ctx.lineTo(segment[i].x, segment[i].y);
                }
                ctx.stroke();
            });

            ctx.restore();

            this.generateLayerTooltips(layer, topBoundary, bottomBoundary, centerLine, thicknessPx[index]);
        }

        this.layerLayout = layout;
    }

    extractConnectedSegments(points) {
        if (!Array.isArray(points)) {
            return [];
        }
        const segments = [];
        let current = [];
        for (const pt of points) {
            if (pt && pt.valid) {
                current.push(pt);
            } else if (current.length > 0) {
                if (current.length > 1) {
                    segments.push(current);
                }
                current = [];
            }
        }
        if (current.length > 1) {
            segments.push(current);
        }
        return segments;
    }

    generateLayerTooltips(layer, topBoundary, bottomBoundary, centerLine, approximateThickness) {
        if (!bottomBoundary || !centerLine) {
            return;
        }

        let activeSegment = null;
        const segments = [];

        for (let i = 0; i < bottomBoundary.length; i++) {
            const bottom = bottomBoundary[i];
            const top = topBoundary ? topBoundary[i] : null;
            const center = centerLine[i];
            const isValid = bottom && bottom.valid && center && center.valid;

            if (isValid) {
                if (!activeSegment) {
                    activeSegment = {
                        startIndex: i,
                        endIndex: i,
                        minX: bottom.x,
                        maxX: bottom.x,
                        minY: Math.min(top ? top.y : bottom.y, bottom.y),
                        maxY: Math.max(top ? top.y : bottom.y, bottom.y),
                        points: [bottom],
                        thickness: approximateThickness || 6
                    };
                } else {
                    activeSegment.endIndex = i;
                    activeSegment.minX = Math.min(activeSegment.minX, bottom.x);
                    activeSegment.maxX = Math.max(activeSegment.maxX, bottom.x);
                    activeSegment.minY = Math.min(activeSegment.minY, top ? top.y : bottom.y, bottom.y);
                    activeSegment.maxY = Math.max(activeSegment.maxY, top ? top.y : bottom.y, bottom.y);
                    activeSegment.points.push(bottom);
                }
            } else if (activeSegment) {
                segments.push(activeSegment);
                activeSegment = null;
            }
        }

        if (activeSegment) {
            segments.push(activeSegment);
        }

        segments.forEach(segment => {
            const width = Math.max(segment.maxX - segment.minX, 6);
            const height = Math.max(segment.maxY - segment.minY, segment.thickness || 6);
            const geometryPoints = segment.points.map(pt => ({ x: pt.x, y: pt.y }));
            const markerRadius = Math.max(Math.min(height * 0.25, 6), 3);

            this.tooltipData.push({
                x: (segment.minX + segment.maxX) / 2,
                y: (segment.minY + segment.maxY) / 2,
                width,
                height,
                geometry: {
                    type: 'polyline',
                    points: geometryPoints,
                    thickness: height
                },
                markerRadius,
                hitRadius: markerRadius + 3,
                data: { type: 'layer', layer }
            });
        });
    }

    getLandElevationAt(km) {
        const landPoints = this.projectData.profile_data?.land_points;
        if (!landPoints || landPoints.length === 0) {
            return null;
        }

        if (km <= landPoints[0].x) {
            return landPoints[0].y;
        }
        if (km >= landPoints[landPoints.length - 1].x) {
            return landPoints[landPoints.length - 1].y;
        }

        for (let i = 0; i < landPoints.length - 1; i++) {
            const current = landPoints[i];
            const next = landPoints[i + 1];
            if (km >= current.x && km <= next.x) {
                const span = next.x - current.x;
                if (span === 0) {
                    return current.y;
                }
                const t = (km - current.x) / span;
                return current.y + (next.y - current.y) * t;
            }
        }
        return landPoints[landPoints.length - 1].y;
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
                    geometry: {
                        type: 'rect',
                        x1,
                        y1: yBridge,
                        x2,
                        y2: yBridge + bridgeHeight + archHeight
                    },
                    markerRadius: 5,
                    hitRadius: 8,
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
        if (!this.projectData.layers || !Array.isArray(this.projectData.layers)) {
            return;
        }
        
        if (!this.layerLayout) {
            this.layerLayout = this.buildLayerLayout();
        }

        const { layers, thicknessPx } = this.layerLayout;
        if (!layers.length) {
            return;
        }
        
        const ctx = this.canvas.ctx;
        const projectStart = parseFloat(this.projectData.start_kilometer) || 0;
        const projectEnd = parseFloat(this.projectData.end_kilometer) || projectStart;
        
        this.projectData.layers.forEach(layer => {
            if (!layer.experiments || !Array.isArray(layer.experiments)) {
                return;
            }

            const layerIndex = this.layerIndexMap.get(layer.id);
            if (layerIndex === undefined) {
                return;
            }
            
            layer.experiments.forEach(experiment => {
                if (!experiment || !this.isExperimentInDateRange(experiment)) {
                    return;
                }
                
                let kmStart = parseFloat(experiment.kilometer_start);
                let kmEnd = parseFloat(experiment.kilometer_end);
                if (!isFinite(kmStart) || !isFinite(kmEnd)) {
                    return;
                }
                
                if (kmEnd < kmStart) {
                    [kmStart, kmEnd] = [kmEnd, kmStart];
                }

                const withinProject =
                    kmStart >= projectStart - 0.001 &&
                    kmEnd <= projectEnd + 0.001;

                if (!withinProject) {
                    const offset = this.originalXMin || 0;
                    kmStart = offset + kmStart;
                    kmEnd = offset + kmEnd;
                }

                const xStart = this.transformX(kmStart);
                const xEnd = this.transformX(kmEnd);
                if (!isFinite(xStart) || !isFinite(xEnd)) {
                    return;
                }
                
                const yStart = this.getLayerYPosition(layerIndex, kmStart);
                const yEnd = this.getLayerYPosition(layerIndex, kmEnd);
                if (yStart === null || yEnd === null) {
                    return;
                }
                
                const color = this.getExperimentColor(experiment);
                const lineWidth = Math.max(thicknessPx[layerIndex] * 0.9, 6);

        ctx.save();
        ctx.beginPath();
                ctx.strokeStyle = color;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.lineWidth = lineWidth;
                ctx.globalAlpha = 0.85;
                ctx.moveTo(xStart, yStart);
                ctx.lineTo(xEnd, yEnd);
            ctx.stroke();
            ctx.restore();

                if (!this.tooltipData) {
                    this.tooltipData = [];
                }
        this.tooltipData.push({
                    x: (xStart + xEnd) / 2,
                    y: (yStart + yEnd) / 2,
                    width: Math.abs(xEnd - xStart) + 14,
                    height: Math.max(lineWidth + 12, 12),
                    geometry: {
                        type: 'segment',
                        x1: xStart,
                        y1: yStart,
                        x2: xEnd,
                        y2: yEnd,
                        thickness: lineWidth
                    },
                    markerRadius: Math.max(Math.min(lineWidth * 0.35, 6), 3),
                    hitRadius: Math.max(Math.min(lineWidth * 0.35, 6), 3) + 3,
            data: {
                        type: 'experiment',
                        experiment,
                        layer,
                        color
                    }
                });
            });
        });
    }

    drawTooltipMarkers() {
        if (!Array.isArray(this.tooltipData) || this.tooltipData.length === 0) {
            return;
        }

        const ctx = this.canvas.ctx;
        ctx.save();
        ctx.lineWidth = 1.4;
        this.tooltipData.forEach(item => {
            if (!Number.isFinite(item?.x) || !Number.isFinite(item?.y)) {
                return;
            }
            const radius = Math.max(item.markerRadius || 4, 3);
            let stroke = '#2563eb';
            let fill = 'rgba(37, 99, 235, 0.18)';

            if (item.data?.type === 'layer') {
                const layer = item.data.layer;
                const isFixed = layer?.state === 1;
                stroke = isFixed ? '#1f2937' : '#fb923c';
                fill = isFixed ? 'rgba(31,41,55,0.16)' : 'rgba(251,146,60,0.18)';
            } else if (item.data?.type === 'experiment') {
                const color = item.data.color || '#64748b';
                stroke = color;
                fill = 'rgba(100,116,139,0.18)';
                if (color.startsWith('#') && color.length === 7) {
                    const r = parseInt(color.slice(1, 3), 16);
                    const g = parseInt(color.slice(3, 5), 16);
                    const b = parseInt(color.slice(5, 7), 16);
                    fill = `rgba(${r}, ${g}, ${b}, 0.2)`;
                }
            } else if (item.data?.type === 'bridge') {
                stroke = '#0ea5e9';
                fill = 'rgba(14,165,233,0.2)';
            }

            ctx.beginPath();
            ctx.arc(item.x, item.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = fill;
            ctx.fill();
            ctx.strokeStyle = stroke;
            ctx.stroke();
        });
        ctx.restore();
    }

    getLayerYPosition(layerIndex, kilometer) {
        if (!this.layerLayout || !this.layerLayout.centers) {
            return null;
        }
        const points = this.layerLayout.centers[layerIndex];
        if (!points || points.length === 0) {
            return null;
        }

        let previous = null;
        for (const point of points) {
            if (!point.valid) {
                continue;
            }
            if (kilometer <= point.km) {
                if (!previous) {
                    return point.y;
                }
                const span = point.km - previous.km;
                if (span <= 0) {
                    return point.y;
                }
                const t = (kilometer - previous.km) / span;
                return previous.y + (point.y - previous.y) * t;
            }
            previous = point;
        }
        return previous ? previous.y : null;
    }

    getExperimentColor(experiment) {
        const status = Number(experiment.status);
        const approval = Number(experiment.approval_status);

        if (status === 2) {
            if (approval === 2) {
                return '#ef4444';
            }
            if (approval === 1) {
                return '#22c55e';
            }
            return '#4ade80';
        }
        if (status === 1) {
            return '#f97316';
        }
        if (status === 3) {
            return '#ef4444';
        }
        return '#e2e8f0';
    }

    getDistanceToTooltipItem(x, y, item) {
        const geom = item.geometry;
        if (!geom) {
            const halfW = (item.width || 0) / 2;
            const halfH = (item.height || 0) / 2;
            const dx = Math.max(Math.abs(x - (item.x || 0)) - halfW, 0);
            const dy = Math.max(Math.abs(y - (item.y || 0)) - halfH, 0);
            return Math.sqrt(dx * dx + dy * dy);
        }

        const thickness = (geom.thickness || 0) / 2;

        if (geom.type === 'segment') {
            const distance = this.pointToSegmentDistance(x, y, geom.x1, geom.y1, geom.x2, geom.y2);
            return Math.max(distance - thickness, 0);
        }

        if (geom.type === 'polyline' && Array.isArray(geom.points)) {
            let minDist = Infinity;
            for (let i = 0; i < geom.points.length - 1; i++) {
                const p1 = geom.points[i];
                const p2 = geom.points[i + 1];
                const distance = this.pointToSegmentDistance(x, y, p1.x, p1.y, p2.x, p2.y);
                if (distance < minDist) {
                    minDist = distance;
                }
            }
            return Math.max(minDist - thickness, 0);
        }

        if (geom.type === 'rect') {
            const cx = (geom.x1 + geom.x2) / 2;
            const cy = (geom.y1 + geom.y2) / 2;
            const dx = Math.max(Math.abs(x - cx) - Math.abs(geom.x2 - geom.x1) / 2, 0);
            const dy = Math.max(Math.abs(y - cy) - Math.abs(geom.y2 - geom.y1) / 2, 0);
            return Math.sqrt(dx * dx + dy * dy);
        }

        return null;
    }

    pointToSegmentDistance(px, py, x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const lengthSquared = dx * dx + dy * dy;

        if (lengthSquared === 0) {
            const distX = px - x1;
            const distY = py - y1;
            return Math.sqrt(distX * distX + distY * distY);
        }

        let t = ((px - x1) * dx + (py - y1) * dy) / lengthSquared;
        t = Math.max(0, Math.min(1, t));

        const projX = x1 + t * dx;
        const projY = y1 + t * dy;
        const distX = px - projX;
        const distY = py - projY;

        return Math.sqrt(distX * distX + distY * distY);
    }

    transformX(x) {
        // تبدیل مختصات X از کیلومتر به پیکسل
        // اضافه کردن margin برای فاصله از لبه چپ
        return this.margin + (x - this.xMin) * this.xScale;
    }

    transformY(y) {
        if (this.yScale === undefined || this.yMax === undefined || this.yMin === undefined) {
            console.error('yScale, yMax, or yMin is undefined!', {
                yScale: this.yScale,
                yMax: this.yMax,
                yMin: this.yMin
            });
            return this.margin + this.height / 2;
        }
        const yRange = this.yMax - this.yMin;
        if (yRange <= 0) {
            return this.margin + this.height / 2;
        }
        const mainCanvasHeight = this.height - this.margin * 2 - 30;
        const normalizedY = (y - this.yMin) / yRange;
        const rawY = this.margin + mainCanvasHeight - (normalizedY * mainCanvasHeight);
        return rawY;
    }

    inverseTransformY(pixelY) {
        if (this.yScale === undefined || this.yMax === undefined || this.yMin === undefined) {
            console.error('inverseTransformY: scale or bounds are undefined!', {
                yScale: this.yScale,
                yMax: this.yMax,
                yMin: this.yMin
            });
            return 0;
        }
        const mainCanvasHeight = this.height - this.margin * 2 - 30;
        const clampedPixelY = Math.min(Math.max(pixelY, this.margin), this.margin + mainCanvasHeight);
        const distanceFromTop = clampedPixelY - this.margin;
        const normalized = distanceFromTop / mainCanvasHeight;
        const value = this.yMax - normalized * (this.yMax - this.yMin);
        return value;
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
        // اطمینان از اینکه مقیاس‌ها محاسبه شده‌اند
        if (this.xScale === undefined || this.yScale === undefined || this.xMin === undefined || this.xMax === undefined) {
            if (!this._scalesCalculated) {
                this.calculateScales();
            }
        }
        
        const realX = this.xMin + (this.mouseX - this.margin) / this.xScale;
        const realY = this.inverseTransformY(this.mouseY);
        if (document.getElementById('xinput')) {
            document.getElementById('xinput').value = realX.toFixed(3);
        }
        if (document.getElementById('yinput')) {
            document.getElementById('yinput').value = realY.toFixed(3);
        }
        
        // فقط tooltip را به‌روزرسانی کن - بدون render کامل
        // این باعث می‌شود که مقیاس‌ها تغییر نکنند و زوم خودکار نداشته باشیم
        // crosshair در render اصلی رسم می‌شود (که فقط یک بار فراخوانی می‌شود)
        this.showProfileTooltip(this.mouseX, this.mouseY);
        this.showTooltip(this.mouseX, this.mouseY);
        
        // render را حذف کردیم - فقط tooltip را به‌روزرسانی می‌کنیم
        // این باعث می‌شود که مقیاس‌ها تغییر نکنند و زوم خودکار نداشته باشیم
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
        if (!tooltip || !this.tooltipData) {
            return;
        }

        let hoveredItem = null;
        let minDistance = Infinity;

        for (const item of this.tooltipData) {
            if (!Number.isFinite(item?.x) || !Number.isFinite(item?.y)) {
                continue;
            }
            const hitRadius = Math.max(item.hitRadius || item.markerRadius || 6, 3);
            const distance = Math.hypot(x - item.x, y - item.y);
            if (!Number.isFinite(distance)) {
                continue;
            }
            if (distance <= hitRadius && distance < minDistance) {
                minDistance = distance;
                hoveredItem = item;
            }
        }

        if (hoveredItem) {
            let html = '';
            const d = hoveredItem.data;
            if (d.type === 'layer') {
                const layer = d.layer;
                const stateMap = {0:'متغیر',1:'ثابت'};
                const stateColor = layer.state === 1 ? '#2563eb' : '#f97316';
                html = `<div style="display:flex;align-items:center;gap:6px;font-weight:bold;">
                    <span style="font-size:18px;color:${stateColor}">▭</span>
                    <span>${layer.name}</span>
                </div>`;
                html += `<div style="font-size:12px;color:#555;">نوع لایه: <b style='color:${stateColor}'>${stateMap[layer.state] || 'نامشخص'}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">ضخامت اسمی: <b>${layer.thickness_cm} cm</b></div>`;
                html += `<div style="font-size:12px;color:#555;">تعداد آزمایش ثبت‌شده: <b>${layer.experiments?.length || 0}</b></div>`;
                if (layer.executed_ranges && layer.executed_ranges.length > 0) {
                    html += `<div style="font-size:12px;color:#555;">بازه‌های فعال: <b>${layer.executed_ranges.length}</b></div>`;
                }
            } else if (d.type === 'bridge') {
                const s = d.structure;
                const statusMap = {0:'شروع نشده',1:'در حال انجام',2:'تکمیل شده'};
                let statusColor = s.status === 2 ? '#7ed957' : s.status === 1 ? '#ffc107' : '#bdbdbd';
                html = `<div style="display:flex;align-items:center;gap:6px;font-weight:bold;"><span style="font-size:18px;color:${statusColor}">🌉</span> <span>${s.name}</span></div>`;
                html += `<div style="font-size:12px;color:#555;">وضعیت: <b style='color:${statusColor}'>${statusMap[s.status]}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">کیلومتر شروع: <b>${s.start_kilometer}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">کیلومتر پایان: <b>${s.end_kilometer}</b></div>`;
                html += `<div style="font-size:12px;color:#555;">طول پل: <b>${(s.end_kilometer-s.start_kilometer).toFixed(2)} km</b></div>`;
            } else if (d.type === 'experiment') {
                const experiment = d.experiment;
                const layer = d.layer;
                const color = d.color || '#94a3b8';
                const statusMap = {0:'در انتظار',1:'در حال انجام',2:'تکمیل شده',3:'رد شده'};
                const approvalMap = {1:'تایید شده',2:'رد شده'};
                html = `<div style="display:flex;align-items:center;gap:6px;">
                    <span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:${color};box-shadow:0 0 8px ${color};"></span>
                    <span style="font-weight:bold;color:${color}">آزمایش ${experiment.experiment_type}</span>
                </div>`;
                html += `<div style="font-size:13px;color:#555;">لایه: <b>${layer.name}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">کیلومتر: <b>${experiment.kilometer_start} تا ${experiment.kilometer_end}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">تاریخ درخواست: <b>${experiment.request_date || 'نامشخص'}</b></div>`;
                html += `<div style="font-size:13px;color:#555;">وضعیت: <b>${statusMap[experiment.status] || 'نامشخص'}</b></div>`;
                if (experiment.approval_status) {
                    const approvalText = approvalMap[experiment.approval_status] || 'در انتظار تایید';
                    html += `<div style="font-size:13px;color:#555;">وضعیت تایید: <b>${approvalText}</b></div>`;
                }
                if (experiment.description) {
                    html += `<div style='font-size:12px;color:#888;margin-top:2px;'>${experiment.description}</div>`;
                }
            }

            tooltip.innerHTML = html;
            tooltip.style.display = 'block';
            const canvas = document.getElementById('mainCanvas');
            const rect = canvas.getBoundingClientRect();
            const pageX = rect.left + window.scrollX + x;
            const pageY = rect.top + window.scrollY + y;
            tooltip.style.left = (pageX + 14) + 'px';
            tooltip.style.top = (pageY + 14) + 'px';
            tooltip.style.background = 'rgba(255,255,255,0.7)';
            tooltip.style.backdropFilter = 'blur(8px)';
            tooltip.style.borderRadius = '8px';
            tooltip.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
            tooltip.style.color = '#222';
            tooltip.style.padding = '10px 14px';
            tooltip.style.fontSize = '13px';
            tooltip.style.pointerEvents = 'none';
            this.hoveredTooltipItem = hoveredItem;
        } else {
            tooltip.style.display = 'none';
            this.hoveredTooltipItem = null;
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

    drawCrosshairOnly() {
        // فقط crosshair و tooltip را رسم کن بدون render کامل
        // این باعث می‌شود که مقیاس‌ها تغییر نکنند
        if (this.mouseX !== null && this.mouseY !== null) {
            // فقط crosshair را رسم کن
            this.drawCrosshair(this.mouseX, this.mouseY);
            // tooltip را نمایش بده
            this.showProfileTooltip(this.mouseX, this.mouseY);
            this.showTooltip(this.mouseX, this.mouseY);
        }
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
            // خط جاده باید روی صفر باشد، نه roadA.y
            const yRoad1 = this.transformY(0);
            const yRoad2 = this.transformY(0);

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

            // اگر اختلاف ارتفاع خیلی کم است، هاشور نزن تا نوار تیره ایجاد نشود
            const avgHeight = (Math.abs(yLand1 - yRoad1) + Math.abs(yLand2 - yRoad2)) / 2;
            if (avgHeight < 6) {
                ctx.restore();
                continue;
            }

            ctx.clip();

            // پرکردن خیلی ملایم به عنوان پس‌زمینه
            const isNeutral = !isExcavation && !isEmbankment;
            if (isNeutral) {
                ctx.restore();
                continue;
            }
            let baseFill = isExcavation ? 'rgba(220, 53, 69, 0.25)' : 'rgba(13, 110, 253, 0.22)';
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            const minY = Math.min(yLand1, yRoad1, yLand2, yRoad2);
            const maxY = Math.max(yLand1, yRoad1, yLand2, yRoad2);
            ctx.fillStyle = baseFill;
            ctx.fillRect(minX - 4, minY - 4, (maxX - minX) + 8, (maxY - minY) + 8);

            // هاشور مورب با زاویه ۴۵ درجه - با ضخامت و تیرگی کمتر
            ctx.strokeStyle = baseFill;
            ctx.globalAlpha = 0.65;
            ctx.lineWidth = Math.min(Math.max(avgHeight / 10, 0.6), 1.1);
            ctx.lineCap = 'round';
            const spacing = Math.max(Math.min(avgHeight * 1.2, 14), 8);
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