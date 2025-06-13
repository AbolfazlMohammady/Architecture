import { Canvas } from './canvas.js';
import { YAxisCanvas } from './yaxiscanvas.js';
import { XAxisCanvas } from './xaxiscanvas.js';

export class RoadCanvasApp {
    constructor({ canvasId, width, height, margin, project }) {
        this.canvasId = canvasId;
        this.width = width;
        this.height = height;
        this.margin = margin;
        this.container = document.getElementById('container');
        this.showRoadLine = true;
        this.showLandLine = true;
        this.showlayerline = true;
        this.showBridge = true;
        this.project = project

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        var xunit = 100;
        var yunit = 43;

        this.canvas = new Canvas({
            containerId: 'container',
            width: this.width,
            height: this.height,
            margin: this.margin,
            start_kilometer:this.project.start_kilometer,
            end_kilometer:this.project.end_kilometer
        });

        this.canvas.clear(); // اینجا بذار، نه توی متدهای دیگر

        this.yAxis = new YAxisCanvas({
            canvasId: 'yAxisCanvas',
            height: this.height,
            width: 50,
            margin: this.margin,
            yunit: yunit
        });

        this.xAxis = new XAxisCanvas({
            canvasId: 'xAxisCanvas',
            width: this.width,
            height: 30,
            margin: this.margin,
            xunit: xunit
        });
        
        let xarray = [];
        var landpoints = []
        var roadpoints = []
        var i =0
        for (let kilometer = this.project.start_kilometer; kilometer < this.project.end_kilometer; kilometer += 0.100) {
            xarray.push(`${kilometer.toFixed(3)}km`);
            landpoints.push(
                {
                    x:this.project.profile_points.profile_points.landpoints[i].x,
                    y:this.project.profile_points.profile_points.landpoints[i].y

                }
            )
            roadpoints.push(
                {
                    x:this.project.profile_points.profile_points.roadpoints[i].x,
                    y:this.project.profile_points.profile_points.roadpoints[i].y
                }
            )
            // اصلاح: از || به جای | برای مقایسه منطقی
            if (xarray.length > 10 || this.project.distance < (this.project.end_kilometer - this.project.start_kilometer)) {
                break;
            }
            i++
        }
        this.xAxis.update(xarray);

        this.yAxis.update([
            '-25m', '-20m', '-15m', '-10m', '-5m', '0m', '5m', '10m', '15m', '20m', '25m'
        ]);

        // var landpoints = this.project.profile_points.profile_points.landpoints
        // var roadpoints = this.project.profile_points.profile_points.roadpoints
        

        if (this.showRoadLine) {
            this.canvas.drawRoadLine(roadpoints);
        }

        if (this.showLandLine) {
            this.canvas.drawLandLine(landpoints);
        }
        
        var layers = [];
        for (let index = 0; index < this.project.layers.length; index++) {
            
            layers.push({
                x:roadpoints[index].x,
                y:this.project.layers[index].order_from_top,
                t:this.project.layers[index].thickness_cm
            })
        }

        if (this.showlayerline) {
            this.canvas.drawLayerLine(layers);
        }

        if (this.showBridge) {
            this.canvas.structure.update(this.project.structure.kilometer_location)
            this.canvas.drawBridge()
            this.canvas.draaBridge(200, 300);
        }
    }

    // دکمه‌های کنترلی برای هر نوع خط
    toggleRoadLine() {
        this.showRoadLine = !this.showRoadLine;
        this.render();
    }

    toggleLandLine() {
        this.showLandLine = !this.showLandLine;
        this.render();
    }

    toggleLayerLine() {
        this.showlayerline = !this.showlayerline;
        this.render();
    }

    toggleBridge() {
        this.showBridge = !this.showBridge;
        this.render();
    }

}
