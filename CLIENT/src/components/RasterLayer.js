import L from "leaflet";
import proj4 from 'proj4';
import { createLayerComponent } from "@react-leaflet/core";
import {parseGeoTiffData} from "../utils/helpers";

if (!Math.bilinearInterpolation) {
    Math.bilinearInterpolation = function (values, x, y) {
        if (x < 0 || y < 0 || x > values.length || y > values[0].length) {
            // console.log(0, x, y)
            return null;
        }
        let x1 = Math.floor(x - 1), y1 = Math.floor(y - 1), x2 = Math.ceil(x + 1), y2 = Math.ceil(y + 1);
        x1 = Math.max(0, x1);
        x2 = Math.max(0, x2);
        y1 = Math.max(0, y1);
        y2 = Math.max(0, y2);
        x1 = Math.min(values.length - 1, x1);
        x2 = Math.min(values.length - 1, x2);
        y1 = Math.min(values[0].length - 1, y1);
        y2 = Math.min(values[0].length - 1, y2);
        // try{
        let q11 = (((x2 - x) * (y2 - y)) / ((x2 - x1) * (y2 - y1))) * values[x1][y1]
        let q21 = (((x - x1) * (y2 - y)) / ((x2 - x1) * (y2 - y1))) * values[x2][y1]
        let q12 = (((x2 - x) * (y - y1)) / ((x2 - x1) * (y2 - y1))) * values[x1][y2]
        let q22 = (((x - x1) * (y - y1)) / ((x2 - x1) * (y2 - y1))) * values[x2][y2]
        return q11 + q21 + q12 + q22
        // }catch(e){
        //     console.log(x1, x2, y1, y2);
        // }
    }
}
if (!Math.nearestNeighbour) {
    Math.nearestNeighbour = function (values, x, y) {
        if (x < 0 || y < 0 || x > values.length || y > values[0].length) {
            return null;
        }
        x = Math.max(Math.floor(x), 0);
        y = Math.max(Math.floor(y), 0);
        x = Math.min(Math.ceil(x), values.length - 1);
        y = Math.min(Math.ceil(y), values[0].length - 1);
        return values[x][y];
    }
}
if (!Math.bicubicInterpolation) {
    Math.bicubicInterpolation = function (values, dx, dy) {

        const createInterpolator = (values, options = {}) => {
            options = Object.assign({
                extrapolate: false,
                scaleX: 1,
                scaleY: 1,
                translateX: 0,
                translateY: 0
            }, options);
            const a00 = values[1][1],
                a01 = (-1 / 2) * values[1][0] + (1 / 2) * values[1][2],
                a02 = values[1][0] + (-5 / 2) * values[1][1] + 2 * values[1][2] + (-1 / 2) * values[1][3],
                a03 = (-1 / 2) * values[1][0] + (3 / 2) * values[1][1] + (-3 / 2) * values[1][2] + (1 / 2) * values[1][3],
                a10 = (-1 / 2) * values[0][1] + (1 / 2) * values[2][1],
                a11 = (1 / 4) * values[0][0] + (-1 / 4) * values[0][2] + (-1 / 4) * values[2][0] + (1 / 4) * values[2][2],
                a12 = (-1 / 2) * values[0][0] + (5 / 4) * values[0][1] + (-1) * values[0][2] + (1 / 4) * values[0][3] + (1 / 2) * values[2][0] + (-5 / 4) * values[2][1] + values[2][2] + (-1 / 4) * values[2][3],
                a13 = (1 / 4) * values[0][0] + (-3 / 4) * values[0][1] + (3 / 4) * values[0][2] + (-1 / 4) * values[0][3] + (-1 / 4) * values[2][0] + (3 / 4) * values[2][1] + (-3 / 4) * values[2][2] + (1 / 4) * values[2][3],
                a20 = values[0][1] + (-5 / 2) * values[1][1] + 2 * values[2][1] + (-1 / 2) * values[3][1],
                a21 = (-1 / 2) * values[0][0] + (1 / 2) * values[0][2] + (5 / 4) * values[1][0] + (-5 / 4) * values[1][2] + (-1) * values[2][0] + values[2][2] + (1 / 4) * values[3][0] + (-1 / 4) * values[3][2],
                a22 = values[0][0] + (-5 / 2) * values[0][1] + 2 * values[0][2] + (-1 / 2) * values[0][3] + (-5 / 2) * values[1][0] + (25 / 4) * values[1][1] + (-5) * values[1][2] + (5 / 4) * values[1][3] + 2 * values[2][0] + (-5) * values[2][1] + 4 * values[2][2] + (-1) * values[2][3] + (-1 / 2) * values[3][0] + (5 / 4) * values[3][1] + (-1) * values[3][2] + (1 / 4) * values[3][3],
                a23 = (-1 / 2) * values[0][0] + (3 / 2) * values[0][1] + (-3 / 2) * values[0][2] + (1 / 2) * values[0][3] + (5 / 4) * values[1][0] + (-15 / 4) * values[1][1] + (15 / 4) * values[1][2] + (-5 / 4) * values[1][3] + (-1) * values[2][0] + 3 * values[2][1] + (-3) * values[2][2] + values[2][3] + (1 / 4) * values[3][0] + (-3 / 4) * values[3][1] + (3 / 4) * values[3][2] + (-1 / 4) * values[3][3],
                a30 = (-1 / 2) * values[0][1] + (3 / 2) * values[1][1] + (-3 / 2) * values[2][1] + (1 / 2) * values[3][1],
                a31 = (1 / 4) * values[0][0] + (-1 / 4) * values[0][2] + (-3 / 4) * values[1][0] + (3 / 4) * values[1][2] + (3 / 4) * values[2][0] + (-3 / 4) * values[2][2] + (-1 / 4) * values[3][0] + (1 / 4) * values[3][2],
                a32 = (-1 / 2) * values[0][0] + (5 / 4) * values[0][1] + (-1) * values[0][2] + (1 / 4) * values[0][3] + (3 / 2) * values[1][0] + (-15 / 4) * values[1][1] + 3 * values[1][2] + (-3 / 4) * values[1][3] + (-3 / 2) * values[2][0] + (15 / 4) * values[2][1] + (-3) * values[2][2] + (3 / 4) * values[2][3] + (1 / 2) * values[3][0] + (-5 / 4) * values[3][1] + values[3][2] + (-1 / 4) * values[3][3],
                a33 = (1 / 4) * values[0][0] + (-3 / 4) * values[0][1] + (3 / 4) * values[0][2] + (-1 / 4) * values[0][3] + (-3 / 4) * values[1][0] + (9 / 4) * values[1][1] + (-9 / 4) * values[1][2] + (3 / 4) * values[1][3] + (3 / 4) * values[2][0] + (-9 / 4) * values[2][1] + (9 / 4) * values[2][2] + (-3 / 4) * values[2][3] + (-1 / 4) * values[3][0] + (3 / 4) * values[3][1] + (-3 / 4) * values[3][2] + (1 / 4) * values[3][3];

            return (x, y) => {
                x = (x * options.scaleX) + options.translateX;
                y = (y * options.scaleY) + options.translateY;

                if (x < 0 || y < 0 || x > 1 || y > 1) throw 'cannot interpolate outside the square from (0, 0) to (1, 1): (' + x + ', ' + y + ')';

                const x2 = x * x,
                    x3 = x * x2,
                    y2 = y * y,
                    y3 = y * y2;

                return (a00 + a01 * y + a02 * y2 + a03 * y3) +
                    (a10 + a11 * y + a12 * y2 + a13 * y3) * x +
                    (a20 + a21 * y + a22 * y2 + a23 * y3) * x2 +
                    (a30 + a31 * y + a32 * y2 + a33 * y3) * x3;
            }
        }

        const createGridInterpolator = (values, options = {}) => {
            let x;
            options = Object.assign({
                extrapolate: false,
                scaleX: 1,
                scaleY: 1,
                translateX: 0,
                translateY: 0
            }, options);

            const m = values.length;
            const n = values[0].length;
            const interpolators = [];

            if (options.extrapolate) {
                //Extrapolate X
                values[-2] = [];
                values[-1] = [];
                values[m] = [];
                values[m + 1] = [];
                for (let y = 0; y < n; y++) {
                    const leftDelta = values[0][y] - values[1][y];
                    const rightDelta = values[m - 1][y] - values[m - 2][y];
                    values[-2][y] = values[0][y] + 2 * leftDelta;
                    values[-1][y] = values[0][y] + leftDelta;
                    values[m][y] = values[m - 1][y] + rightDelta;
                    values[m + 1][y] = values[m - 1][y] + 2 * rightDelta;
                }

                //Extrapolate Y
                for (x = -2; x < m + 2; x++) {
                    const bottomDelta = values[x][0] - values[x][1];
                    const topDelta = values[x][n - 1] - values[x][n - 2];
                    values[x][-2] = values[x][0] + 2 * bottomDelta;
                    values[x][-1] = values[x][0] + bottomDelta;
                    values[x][n] = values[x][n - 1] + topDelta;
                    values[x][n + 1] = values[x][n - 1] + 2 * topDelta;
                }

                //Populate interpolator arrays
                for (x = -1; x < m; x++) interpolators[x] = [];
            } else {
                //Populate interpolator arrays
                for (x = 1; x < m - 2; x++) interpolators[x] = [];
            }

            return (x, y) => {
                x = (x * options.scaleX) + options.translateX;
                y = (y * options.scaleY) + options.translateY;

                if (options.extrapolate) {
                    if (x < -1 || y < -1 || x > m || y > n) throw 'cannot interpolate outside the rectangle from (-1, -1) to (' + m + ', ' + n + ') even when extrapolating: (' + x + ', ' + y + ')';
                } else {
                    if (x < 1 || y < 1 || x > m - 2 || y > n - 2) throw 'cannot interpolate outside the rectangle from (1, 1) to (' + (m - 2) + ', ' + (n - 2) + '): (' + x + ', ' + y + '), you might want to enable extrapolating';
                }

                let blX = Math.floor(x);// The position of interpolator's (0, 0) for this point
                let blY = Math.floor(y);

                if (options.extrapolate) {//If you're trying to interpolate on the top or right edges of what can be interpolated, you have to interpolate in the region to the left or bottom respectively.
                    if (x === m) blX--;
                    if (y === n) blY--;
                } else {
                    if (x === m - 2) blX--;
                    if (y === n - 2) blY--;
                }


                if (!interpolators[blX][blY]) {
                    interpolators[blX][blY] = createInterpolator([
                        [values[blX - 1][blY - 1], values[blX - 1][blY], values[blX - 1][blY + 1], values[blX - 1][blY + 2]],
                        [values[blX][blY - 1], values[blX][blY], values[blX][blY + 1], values[blX][blY + 2]],
                        [values[blX + 1][blY - 1], values[blX + 1][blY], values[blX + 1][blY + 1], values[blX + 1][blY + 2]],
                        [values[blX + 2][blY - 1], values[blX + 2][blY], values[blX + 2][blY + 1], values[blX + 2][blY + 2]]
                    ], {
                        translateX: -blX,
                        translateY: -blY
                    });
                }
                const interpolator = interpolators[blX][blY];

                return interpolator(x, y);
            }
        }

        return createGridInterpolator(values)(dx, dy);
    }
}

// noinspection JSUnresolvedVariable
L.GridLayer.RasterLayer = L.GridLayer.extend({

    initialize: async function (data, options) {
        this.pendingTiles = {};
        if(data.constructor && data.constructor.name && data.constructor.name === 'ArrayBuffer'){
            this.data = await parseGeoTiffData(data);
        }else{
            this.data = data;
        }

        // this.data = (data);
        this.sampleTileRatio = 4
        this.imageSmoothing = false
        this.interpolation = "nearestNeighbour"
        this.debug = false
        if (options) {
            if (options.colorRamp)
                this.colorRamp = options.colorRamp;
            if (options['interpolation'])
                this.interpolation = options['interpolation']
            if (options['samplingRatio'])
                this.sampleTileRatio = options['samplingRatio'];
            if (options['imageSmoothing'])
                this.imageSmoothing = options['imageSmoothing'];
            if (options['debug'])
                this.debug = options['debug'];
        }
        this.samplePerTile = 256 / this.sampleTileRatio;
        // noinspection JSUnresolvedVariable
        L.Util.setOptions(this, options);

        if(Object.keys(this.pendingTiles).length>0){
            for(let i=0;i<Object.keys(this.pendingTiles).length;i++){
                let pt = this.pendingTiles[Object.keys(this.pendingTiles)[i]];
                this.drawTiles(pt.coords, pt.tile, pt.size).then(t=>pt.done(null, t));
            }
        }
    },

    toLatLng: function (coords) {
        return proj4(proj4.defs('EPSG:3857'), proj4.defs('EPSG:4326'), coords);
    },

    toLatLngBbox: function (bbox) {
        const p1 = this.toLatLng([bbox[0], bbox[1]]);
        const p2 = this.toLatLng([bbox[2], bbox[3]]);
        return [...p1, ...p2];
    },

    createTile: function (coords, done) {
        // let done = null;
        if (this.debug) console.time(`TILE:${coords.x}/${coords.y}/${coords.z}`)
        // noinspection JSUnresolvedVariable
        const tile = L.DomUtil.create('canvas', 'leaflet-tile');
        // noinspection JSUnresolvedFunction
        const size = this.getTileSize();
        tile.width = size.x;
        tile.height = size.y;

        if (!this.data){
            this.pendingTiles[`tile${coords.x}${coords.y}${coords.z}`] = {
                tile: tile,
                size: size,
                coords: coords,
                done: done
            }
            return tile;
        }

        this.drawTiles(coords, tile, size).then(t=>done(null, t));
        return tile;
    },

    toWebMer: function (coords) {
        return proj4(proj4.defs('EPSG:4326'), proj4.defs('EPSG:3857'), coords);
    },

    toWebMerBbox: function (bbox) {
        const p1 = this.toWebMer([bbox[0], bbox[1]]);
        const p2 = this.toWebMer([bbox[2], bbox[3]]);
        return [...p1, ...p2];
    },

    tileToLatLngBbox: function (x, y, z) {
        const lng1 = (x / Math.pow(2, z) * 360 - 180);
        const lng2 = ((x + 1) / Math.pow(2, z) * 360 - 180)
        const n1 = Math.PI - 2 * Math.PI * y / Math.pow(2, z);
        const n2 = Math.PI - 2 * Math.PI * (y + 1) / Math.pow(2, z);
        const lat1 = ((180 / Math.PI * Math.atan(0.5 * (Math.exp(n1) - Math.exp(-n1)))));
        const lat2 = ((180 / Math.PI * Math.atan(0.5 * (Math.exp(n2) - Math.exp(-n2)))));
        return [lng1, lat1, lng2, lat2]
    },

    isInsideData: function (box1) {
        switch (this.data['coordinateSystem']) {
            case 4326:
                box1 = this.toLatLngBbox(box1)
                break;
            case 3857:
                box1 = (box1)
                break;
            default:
                throw "Error: Unsupported CRS"
        }
        let box2 = [this.data.x1, this.data.y1, this.data.x2, this.data.y2];
        let aLeftOfB = box1[2] < box2[0];
        let aRightOfB = box1[0] > box2[2];
        let aAboveB = box1[3] > box2[1];
        let aBelowB = box1[1] < box2[3];

        return !(aLeftOfB || aRightOfB || aAboveB || aBelowB);
    },

    drawTiles: function (coords, tile, size) {
        return new Promise(resolve => {
            const ctx = tile.getContext('2d');
            const bbox = this.toWebMerBbox(this.tileToLatLngBbox(coords.x, coords.y, coords.z));
            if (!this.isInsideData(bbox)) {
                if (this.debug) console.timeEnd(`TILE:${coords.x}/${coords.y}/${coords.z}`)
                return;
            }
            const xRes = (bbox[2] - bbox[0]) / this.samplePerTile;
            const yRes = (bbox[3] - bbox[1]) / this.samplePerTile;
            const width = this.samplePerTile,
                height = this.samplePerTile,
                buffer = new Uint8ClampedArray(width * height * 4);
            for (let y = 0; y < size.y; y += this.sampleTileRatio) {
                for (let x = 0; x < size.x; x += this.sampleTileRatio) {
                    let [xi, yi] = this.getDataIndexes(bbox, x, y, xRes, yRes);
                    let v = 0;
                    if (xi <= 0 || yi <= 0 || xi >= this.data.nx || yi >= this.data.ny) {
                        v = null;
                    } else {
                        if (this.interpolation === "nearestNeighbour") {
                            v = Math.nearestNeighbour(this.data.rasterData, yi, xi);
                        }
                        if (this.interpolation === "bilinearInterpolation") {
                            v = Math.bilinearInterpolation(this.data.rasterData, yi, xi);
                        }
                        if (this.interpolation === 'bicubicInterpolation') {
                            if (xi < 2 || yi < 2 || xi >= this.data.nx - 2 || yi >= this.data.ny - 2) {
                                v = Math.nearestNeighbour(this.data.rasterData, yi, xi);
                            } else {
                                try {
                                    v = Math.bicubicInterpolation(this.data.rasterData, yi, xi);
                                } catch (e) {
                                    console.log(this.data.nx, this.data.ny, e)
                                }
                            }
                        }
                    }
                    v = this.getColor(v);
                    let pos = ((y / this.sampleTileRatio * this.samplePerTile) + x / this.sampleTileRatio) * 4;
                    buffer[pos] = v[0];
                    buffer[pos + 1] = v[1];
                    buffer[pos + 2] = v[2];
                    buffer[pos + 3] = v[3];
                }
            }
            const canvas = document.createElement('canvas'), ctxTemp = canvas.getContext('2d');
            canvas.width = width;
            canvas.height = height;
            const iData = ctxTemp.createImageData(width, height);
            iData.data.set(buffer);
            ctxTemp.imageSmoothingEnabled = false;
            ctxTemp.putImageData(iData, 0, 0);

            ctx.imageSmoothingEnabled = this.imageSmoothing;
            ctx.imageSmoothingQuality = 'low';
            ctx.scale(this.sampleTileRatio, this.sampleTileRatio);
            ctx.drawImage(canvas, 0, 0);

            if (this.debug) console.timeEnd(`TILE:${coords.x}/${coords.y}/${coords.z}`)
            resolve(tile)
        })
    },

    getDataIndexes: function (bbox, x, y, xRes, yRes) {
        let lng, lat, coordinates = [0, 0];
        switch (this.data['coordinateSystem']) {
            case 4326:
                coordinates = this.toLatLng([bbox[0] + x * xRes / this.sampleTileRatio, bbox[1] + y * yRes / this.sampleTileRatio]);
                break;
            case 3857:
                coordinates = ([bbox[0] + x * xRes / this.sampleTileRatio, bbox[1] + y * yRes / this.sampleTileRatio]);
                break;
            default:
                throw "Error: Unsupported CRS";
        }
        lng = coordinates[0];
        lat = coordinates[1];
        return [((lng - this.data.x1) / this.data.xRes), ((lat - this.data.y1) / this.data.yRes)];
    },

    getColor: function (value) {
        if (value === null) {
            return [0, 0, 0, 0];
        }
        try {
            let colorRamp = [
                // [0, 0, 255, 150],
                // [0, 125, 255, 150],
                // [0, 255, 255, 150],
                // [0, 255, 125, 150],
                // [0, 255, 0, 150],
                // [125, 255, 0, 150],
                // [255, 255, 0, 150],
                // [255, 125, 0, 150],
                // [255, 0, 0, 150]
                [0, 0, 0, 255],
                [255, 255, 255, 255]
            ];
            if (this.colorRamp)
                colorRamp = this.colorRamp.map(v=>this.hexToRgb(v));
            const colorRampSize = colorRamp.length;
            const rampRatio = (1 / (colorRampSize - 1));
            const overAllRatio = (value - this.data.min) / (this.data.max - this.data.min);
            const index = Math.floor(overAllRatio / rampRatio);
            const startColor = colorRamp[index];
            const endColor = (index + 1) >= colorRamp.length ? colorRamp[index] : colorRamp[index + 1];
            const startColorX = index * rampRatio;//startColor[4]/100;
            const endColorX = (index + 1) * rampRatio;//endColor[4]/100;
            const localRatio = (overAllRatio - startColorX) / (endColorX - startColorX);
            return this.getColorAtRatio(endColor, startColor, localRatio);
        } catch (e) {
            return [0, 0, 0, 0]
        }
    },
    getColorAtRatio: function (startColor, endColor, ratio) {
        const w = ratio * 2 - 1;
        const w1 = (w + 1) / 2;
        const w2 = 1 - w1;
        return [Math.round(startColor[0] * w1 + endColor[0] * w2),
            Math.round(startColor[1] * w1 + endColor[1] * w2),
            Math.round(startColor[2] * w1 + endColor[2] * w2),
            Math.round((startColor[3] * w1 + endColor[3] * w2))];
    },
    componentToHex: function(c) {
        const hex = c.toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    },
    rgbToHex: function(r, g, b) {
        return "#" + this.componentToHex(r) + this.componentToHex(g) + this.componentToHex(b);
    },
    hexToRgb: function(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        let rgba = result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16),
            a: parseInt(result[4], 16)
        } : null;
        if (!rgba)
            return rgba;
        return [rgba.r, rgba.g, rgba.b, rgba.a]
    }

});

// @ts-ignore
L.GridLayer.rasterLayer = function(props) {
    // @ts-ignore
    return new L.GridLayer.RasterLayer(props.data, props.options);
}

// @ts-ignore
const createRasterLayer = (props, context) => {
    // @ts-ignore

    const instance = L.GridLayer.rasterLayer(props);
    // const instance = L.tileLayer.rasterLayer(props.url, {...props});
    return {instance, context};
}

// @ts-ignore
const updateRasterLayer = (instance, props, prevProps) => {
    if (prevProps.data !== props.data) {
        if (instance.setData) instance.setData(props.data)
    }
    if (prevProps.options !== props.options) {
        if (instance.setOptions) instance.setOptions(props.options)
    }
}



const RasterLayer = createLayerComponent(createRasterLayer, updateRasterLayer);

export default RasterLayer;
/**
 * x1
 * y1
 * x2
 * y2
 * nx
 * ny
 * rasterData
 * xRes
 * yRes
 * min
 * max
 * coordinateSystem
 **/