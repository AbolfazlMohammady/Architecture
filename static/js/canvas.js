import { RoadLine } from './roadline.js';  // فرض بر اینه که فایلش رو جدا گذاشتی
import { LandLine } from './landline.js';
import { LayerLine } from './layerline.js';
import { Structure } from './structure.js';


export class Canvas {
  constructor({containerId, width, height, margin,start_kilometer,end_kilometer }) {
    this.container = document.getElementById(containerId);
    this.width = width;
    this.height = height;
    this.margin = margin;

    
    this.canvas = document.getElementById('mainCanvas');
    
    // افزایش کیفیت canvas با devicePixelRatio (حداقل 2 برای کیفیت بالا)
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;

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
    
    
    // this.container.appendChild(this.canvas);

    this.roadLine = new RoadLine({ canvasId: 'mainCanvas',start_kilometer:start_kilometer,end_kilometer:end_kilometer });
    this.landLine = new LandLine({ canvasId: 'mainCanvas',start_kilometer:start_kilometer,end_kilometer:end_kilometer });  // اضافه کردن LandLine
    this.layerLine = new LayerLine({ canvasId: 'mainCanvas',start_kilometer:start_kilometer,end_kilometer:end_kilometer  });
    this.structure = new Structure({ canvasId: 'mainCanvas',structure_type:"bridge" });
 
  }

  drawStructure(position){
    this.structure.update(position);
  }

  drawLayerLine(points){
    this.layerLine.update(points)
  }

  drawRoadLine(points) {
    this.roadLine.update(points);
  }

  drawLandLine(points) {
    this.landLine.update(points);
  }

  resize(width, height) {
    this.width = width;
    this.height = height;
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.ctx = this.canvas.getContext('2d', {
      alpha: true,
      desynchronized: false,
      willReadFrequently: false
    });
    this.ctx.scale(dpr, dpr);
    this.ctx.imageSmoothingEnabled = true;
    this.ctx.imageSmoothingQuality = 'high';
  }
  clear() {
    // پاک کردن canvas - چون ctx.scale(dpr, dpr) تنظیم شده، از width و height منطقی استفاده می‌کنیم
    // اما باید مطمئن شویم که کل canvas پاک می‌شود
    // ذخیره transform فعلی
    this.ctx.save();
    // بازنشانی transform
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    // پاک کردن کل canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    // بازگرداندن transform
    this.ctx.restore();
}

}
