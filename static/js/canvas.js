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
    
    // افزایش کیفیت canvas با devicePixelRatio
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';

    this.ctx = this.canvas.getContext('2d');
    
    // تنظیم scale برای کیفیت بالا
    this.ctx.scale(dpr, dpr);
    
    // بهبود کیفیت رندرینگ
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
  clear() {
    // پاک کردن canvas - چون scale تنظیم شده، از width و height اصلی استفاده می‌کنیم
    this.ctx.clearRect(0, 0, this.width, this.height);
}

}
