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
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    // پاک کردن canvas با در نظر گیری devicePixelRatio
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.restore();
    // scale قبلاً در constructor تنظیم شده است

    ctx.strokeStyle = '#666';
    ctx.lineWidth = 1.5;

    // خط افقی محور X
    ctx.beginPath();
    ctx.moveTo(0, this.height - 19 - this.margin);
    ctx.lineTo(this.width, this.height - 19 - this.margin);
    ctx.stroke();

    ctx.fillStyle = '#000';
    ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';

    // لیبل‌گذاری پویا بر اساس طول بازه
    const range = this.end_km - this.start_km;
    // استفاده از data که از drawAxes می‌آید (اگر موجود باشد)
    let labels = [];
    if (this.data && this.data.length > 0) {
      // استفاده از data که قبلاً در drawAxes تنظیم شده
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
    labels.forEach((km) => {
      // محاسبه موقعیت X بر اساس xScale و xMin (مثل transformX)
      // اگر xScale و xMin موجود باشند، از آنها استفاده کن
      let x;
      if (this.xScale !== null && this.xScale !== undefined && this.xMin !== null && this.xMin !== undefined) {
        // استفاده از همان فرمول transformX
        x = this.margin + (km - this.xMin) * this.xScale;
      } else {
        // fallback: استفاده از روش قبلی
        x = this.margin + ((km - this.start_km) / range) * (this.width - this.margin * 2);
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
      // رسم لیبل اگر x در محدوده canvas است (حتی اگر منفی باشد، برای اسکرول)
      // اما فقط اگر x در محدوده منطقی است (نه خیلی دور)
      if (x >= -100 && x <= this.width + 100) {
        ctx.fillText(kmLabel, x, this.height - 18);
        // خط کوچک زیر لیبل
        ctx.beginPath();
        ctx.moveTo(x, this.height - 19 - this.margin);
        ctx.lineTo(x, this.height - 14 - this.margin);
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
      ctx.restore();
    });
  }
}