export class XAxisCanvas {
  constructor({canvasId, width, height, margin = 5,xunit}) {
    this.canvas = document.getElementById(canvasId);
    this.width = width;
    this.height = height;
    this.margin = margin;
    this.xunit = xunit

    // افزایش کیفیت canvas با devicePixelRatio (حداقل 2)
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    
    this.ctx = this.canvas.getContext('2d', {
      alpha: true,
      desynchronized: false,
      willReadFrequently: false
    });
    
    // تنظیم scale برای کیفیت بالا
    this.ctx.scale(dpr, dpr);
    
    // بهبود کیفیت رندرینگ - حرفه‌ای
    this.ctx.imageSmoothingEnabled = true;
    this.ctx.imageSmoothingQuality = 'high';
    this.ctx.textRenderingOptimization = 'optimizeQuality';

    this.data = [];
  }

  update(data, start_km, end_km, xScale, xMin) {
    this.data = data;
    this.start_km = start_km;
    this.end_km = end_km;
    this.xScale = xScale;
    this.xMin = xMin;
    
    // به‌روزرسانی عرض canvas از style.width
    const canvasElement = this.canvas;
    if (canvasElement && canvasElement.style.width) {
      const newWidth = parseInt(canvasElement.style.width);
      if (newWidth && newWidth > 0) {
        // همیشه canvas را با عرض جدید تنظیم کن
        this.width = newWidth;
        const dpr = Math.max(window.devicePixelRatio || 1, 2);
        this.canvas.width = this.width * dpr;
        this.canvas.style.width = this.width + 'px';
        // تنظیم مجدد context
        this.ctx = this.canvas.getContext('2d', {
          alpha: true,
          desynchronized: false,
          willReadFrequently: false
        });
        this.ctx.scale(dpr, dpr);
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
        this.ctx.textRenderingOptimization = 'optimizeQuality';
      }
    }
    
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    // پاک کردن canvas
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.restore();

    // استفاده از عرض واقعی canvas
    const actualCanvasWidth = this.canvas ? parseInt(this.canvas.style.width) || this.width : this.width;

    ctx.strokeStyle = '#666';
    ctx.lineWidth = 1.5;
    ctx.fillStyle = '#000';
    ctx.font = 'bold 14px Vazirmatn, Tahoma, Arial, sans-serif';
    ctx.textBaseline = 'top';
    ctx.textAlign = 'center';

    // لیبل‌گذاری پویا بر اساس طول بازه
    const range = this.end_km - this.start_km;
    // استفاده از data که از drawAxes می‌آید (اگر موجود باشد)
    let labels = [];
    if (this.data && this.data.length > 0) {
      labels = this.data;
    } else {
      // fallback: تنظیم step بر اساس طول پروژه
      let step;
      if (range <= 5) {
        step = 0.5;
      } else if (range <= 20) {
        step = 1;
      } else if (range <= 50) {
        step = 2;
      } else if (range <= 100) {
        step = 5;
      } else {
        step = 10;
      }
      for (let km = this.start_km; km <= this.end_km + 0.0001; km += step) {
        let label = Math.round(km * 10) / 10;
        labels.push(label);
      }
    }
    
    // رسم همه لیبل‌ها - بدون محدودیت
    const baselineY = this.height - 12;
    const labelY = baselineY - 18;

    labels.forEach((km) => {
      // محاسبه موقعیت X بر اساس xScale و xMin (مثل transformX)
      let x;
      if (this.xScale !== null && this.xScale !== undefined && this.xMin !== null && this.xMin !== undefined) {
        // استفاده از همان فرمول transformX
        x = this.margin + (km - this.xMin) * this.xScale;
      } else {
        // fallback: استفاده از روش قبلی
        x = this.margin + ((km - this.start_km) / range) * (actualCanvasWidth - this.margin * 2);
      }
      
      // تبدیل عدد به فارسی
      let kmLabel = km.toString().replace('.', '٫').replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
      
      ctx.save();
      ctx.font = 'bold 14px Vazirmatn, Tahoma, Arial, sans-serif';
      ctx.fillStyle = '#000';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.shadowColor = '#fff';
      ctx.shadowBlur = 2;
      
      // رسم لیبل - همه لیبل‌ها را نمایش بده (بدون محدودیت)
      ctx.fillText(kmLabel, x, labelY);
      
      // خط کوچک زیر لیبل
      ctx.beginPath();
      ctx.moveTo(x, baselineY - 4);
      ctx.lineTo(x, baselineY + 4);
      ctx.stroke();
      
      ctx.shadowBlur = 0;
      ctx.restore();
    });
    
    // رسم خط افقی محور X در کل عرض canvas
    ctx.beginPath();
    ctx.moveTo(this.margin, baselineY);
    ctx.lineTo(actualCanvasWidth - this.margin, baselineY);
    ctx.stroke();
  }
}