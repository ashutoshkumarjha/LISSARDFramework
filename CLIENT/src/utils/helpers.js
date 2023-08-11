
import GeoTIFF, { fromUrl, fromUrls, fromArrayBuffer, fromBlob } from 'geotiff';

export const generateId = (length) => {
    let result = '';
    const characters = '0123456789';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++ ) {
        result += characters.charAt(Math.floor(Math.random() *
            charactersLength));
    }
    return result;
}

export const parseGeoTiffData = async (ab) => {
    const tiff = await fromArrayBuffer(ab);
    const image = await tiff.getImage();
    const bbox = image.getBoundingBox();
    const x1 = bbox[0],
        y1 = bbox[3],
        x2 = bbox[2],
        y2 = bbox[1],
        xRes = image.getResolution()[0],
        yRes = image.getResolution()[1],
        nx = image.getWidth(),
        ny = image.getHeight();

    let data = {
        x1, y1, x2, y2, xRes, yRes, nx, ny,
        min: null,
        max: null,
        coordinateSystem: image.geoKeys["GeographicTypeGeoKey"]  || image.geoKeys["ProjectedCSTypeGeoKey"],
        rasterData: []
    };

    let bands = await image.readRasters();

    const nb = bands.length;

    if (nb===0){
        return
    }

    for (let bandNo = 0; bandNo < bands.length; bandNo++) {
        const band = bands[bandNo];
        data.rasterData = [];
        for (let y = 0; y < ny; y++) {
            data.rasterData[y] = [];
            for (let x = 0; x < nx; x++) {
                const v = band[(y*bands.width)+x];
                if (data.min===null || data.min > v)
                    data.min = v;
                if (data.max===null || data.max < v)
                    data.max = v;
                data.rasterData[y][x] = v;
            }
        }
    }
    return data;
}

function pointGeomQueryEsriFeatureLayer(featureLayerUrl, id, success, failure) {
    let data = {
        "where": "id=" + id,
        "geometry": '',
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultType": "none",
        "distance": "0.0",
        "units": "esriSRUnit_Meter",
        "returnGeodetic": "false",
        "outFields": "*",
        "returnGeometry": "true",
        "returnCentroid": "false",
        "featureEncoding": "esriDefault",
        "multipatchOption": "xyFootprint",
        "applyVCSProjection": "false",
        "returnIdsOnly": "false",
        "returnUniqueIdsOnly": "false",
        "returnCountOnly": "false",
        "returnExtentOnly": "false",
        "returnQueryGeometry": "false",
        "returnDistinctValues": "false",
        "cacheHint": "false",
        "returnZ": "false",
        "returnM": "false",
        "returnExceededLimitFeatures": "true",
        "sqlFormat": "none",
        "f": "geojson",
        // "resultRecordCount": 1
    };
    let formData = new FormData();
    Object.keys(data).map(k=>{
        formData.append(k, data[k]);
    })
    fetch(featureLayerUrl, {
        method: 'POST',
        body: formData
    }).then(r=>r.json()).then(result=>{
        return success(result.features);
    })
        .catch(e=>{
            console.log(e);
            return failure(e);
        });
}

const loadParcelById = (parcelId) => {
    return new Promise((resolve, reject) => {
        pointGeomQueryEsriFeatureLayer(
            'https://services.arcgis.com/xdsHIIxuCWByZiCB/ArcGIS/rest/services/LINZ_NZ_Primary_Parcels/FeatureServer/0/query',
            parcelId,
            (result)=>{
                // console.log(result);
                resolve(result);
            },
            (err)=>{
                console.log(err);
                reject(err);
            }
        )
    })
}

export const loadparcelIdFromAddressId = async (addressId) => {
    const url = 'https://data.linz.govt.nz/services;key=090cb5ff348b438aac49f2df6ca09256/wfs/table-53324?service=WFS&request=GetFeature&PROPERTYNAME=address_id,parcel_id&CQL_FILTER=address_id='+addressId+'&typename=data.linz.govt.nz:table-53324&outputformat=application/json';
    let result = await fetchGet(url);
    if(result.features.length>0){
        let parcelId = result.features[0].properties['parcel_id'];
        let parcels = await loadParcelById(parcelId);
        if(parcels.length>0){
            let parcel = parcels[0];
            return parcel;
        }
    }
    return null;
}

export const fetchGetWithSignal = (url, signal) => {
    return new Promise((resolve, reject) => {
        fetch(url, {
            method: 'GET',
            signal: signal
        }).then(r=>r.json()).then(result=>{
            return resolve(result);
        })
            .catch(e=>{
                console.log(e);
                return reject(e);
            });
    })
}

export const fetchPost = (url, data, signal) => {
    return new Promise((resolve, reject) => {
        fetch(url, {
            method: 'POST',
            body: data,
            signal: signal
        }).then(r=>r.json()).then(result=>{
            // console.log(result.features);
            return resolve(result.features);
        })
            .catch(e=>{
                console.log(e);
                return reject(e);
            });
    })
}

export const fetchGet = (url) => {
    return new Promise((resolve, reject) => {
        fetch(url, {
            method: 'GET'
        }).then(r=>r.json()).then(result=>{
            return resolve(result);
        })
            .catch(e=>{
                console.log(e);
                return reject(e);
            });
    })
}