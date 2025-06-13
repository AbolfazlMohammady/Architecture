export class LayerLine {
    constructor({ canvasId, start_kilometer, end_kilometer }) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.layers = [];
        this.start_kilometer = start_kilometer
        this.end_kilometer = end_kilometer
    }

    update(layers) {
        this.layers = layers;
        this.draw();
    }

    setStatus(x, newStatus) {
        const layer = this.layers.find(l => l.x === x);
        if (layer) {
            layer.status = newStatus;
            this.draw();  // دوباره رسم کن
        }
    }
    draw() {
        const ctx = this.ctx;
        ctx.fillStyle = 'transparent';
        if (!this.layers || this.layers.length === 0) return;

        const thicknessScale = (this.canvas.height / 50); // پیکسل به ازای هر متر

        // مرتب‌سازی لایه‌ها براساس order (کوچکتر بالاتر)
        const sortedLayers = [...this.layers].sort((a, b) => a.y - b.y);

let currentDepthM = 0; // از سطح جاده به پایین، به متر

        const layer = sortedLayers[0];
        const heightInMeters = layer.t / 100;
        const y = this.canvas.height / 2

        const x = 0;
        const width = this.canvas.width;
        const height = heightInMeters * thicknessScale;
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 1;

        // ctx.fillRect(x, y, width, height);
        ctx.strokeRect(x, y, width, height);

        currentDepthM += heightInMeters;
        

        for (let i = 1; i < sortedLayers.length; i++) {
            const layer = sortedLayers[i];

            const heightInMeters = layer.t / 100;
            const centerDepthM = currentDepthM + (heightInMeters / 2);
            const centerY = this.heightToY(centerDepthM);

            const height = heightInMeters * thicknessScale;
            const y = centerY + height / 2;

            const x = 0;
            const width = this.canvas.width;

            // رنگ بر اساس status
            switch (layer.status) {
                case 'approved':
                    ctx.fillStyle = 'rgba(0, 102, 255, 0.5)';
                    break;
                case 'invalid':
                    ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
                    break;
                case 'pending':
                default:
                    ctx.fillStyle = 'transparent';
                    break;
            }

            ctx.strokeStyle = 'black';
            ctx.lineWidth = 1;

            ctx.fillRect(x, y, width, height);
            ctx.strokeRect(x, y, width, height);

            currentDepthM += heightInMeters;
        }
    }


    heightToY(currentDepthCm) {
        return ((this.canvas.height / 2) + currentDepthCm);
    }


    kmToX(xInMeters) {
        const xKm = xInMeters / 1000; // مثلاً 30100 → 30.1
        const range = 1

        const relativeKm = xKm - this.start_kilometer;
        const ratio = relativeKm / range;

        console.log(`xInMeters: ${xInMeters}, xKm: ${xKm}, ratio: ${ratio}`);

        return ratio * this.canvas.width;
    }

}
