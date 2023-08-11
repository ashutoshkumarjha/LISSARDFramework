
import { MapContainer, TileLayer, WMSTileLayer, useMap, GeoJSON, useMapEvent, Popup, Marker } from 'react-leaflet';
import { connect, useDispatch } from "react-redux";
import L from 'leaflet';
import React, { useEffect, useState } from "react";
// import {TileLayerWMS} from "leaflet/src/layer/tile/TileLayer.WMS";

// import {addLayer, addSearchLayer, changeMapView} from "../actions";
import { BasemapLayer, FeatureLayer } from "react-esri-leaflet";
import Config from '../config.js';

import RasterLayer from "./RasterLayer";
import { addLayer, addSearchLayer, changeMapView, changeMapZoom, mapViewWasSet, updateChartData } from "../actions";
import { generateId } from "../utils/helpers";

const mapStateToProps = state => {
    return {
        map: state.MapReducer
    }
};

function ChangeMapZoom({ zoom }) {
    const map = useMap();
    map.setZoom(zoom);
    return null;
}

function ChangeMapView({ zoom, center, changeMapView }) {
    const map = useMap();
    if (changeMapView) {
        map.setView(center, zoom);
    }
    return null;
}
function ChangeMapExtent({ extent, changeMapView }) {
    const map = useMap();
    if (changeMapView) {
        map.fitBounds(extent);
    }
    return null;
}

function MapViewChangeEvent() {
    const dispatch = useDispatch();
    const map = useMapEvent('moveend', () => {
        dispatch(mapViewWasSet(map.getCenter(), map.getZoom(), map.getBounds()))
    })
    return null
}


const MapLayers = (props) => {
    let layers = Object.keys(props.map.layers).map(layerId => props.map.layers[layerId]);
    layers = layers.sort((a, b) => { return a.sortOrder - b.sortOrder });

    return <div>
        {
            layers.map(layer => {
                if (!layer.active)
                    return '';
                switch (layer.type) {
                    case 'WMS':
                        return props.map.zoom >= layer.minZoom ? <WMSTileLayer
                            maxZoom={24} key={layer.id} url={layer.url} params={{
                                layers: layer.id,
                                format: 'image/png',
                                transparent: true,
                            }} /> : ''
                    case 'VECTOR':
                        return <GeoJSON attribution="&copy; credits due..." data={layer.data} key={layer.id} />
                    case 'RASTER':
                        return <RasterLayer key={layer.id} data={layer.data} options={{
                            interpolation: 'nearestNeighbour',
                            samplingRatio: 4,
                            imageSmoothing: false,
                            debug: false
                        }} />
                    case 'TILE':
                        return <TileLayer key={layer.id}
                            url={layer.url}
                            maxZoom={24}
                        />

                    case 'DATA_TILE':
                        return <TileLayer key={layer.id}
                            url={`${Config.DATA_HOST}/tilem/${layer.dsId}/{z}/{x}/{y}.png?tIndexes=${layer.tIndexes.join(",")}&bands=${layer.style.bands.join(",")}&vmin=${layer.style.min}&vmax=${layer.style.max}&aoi_code=${layer.aoiCode}`}
                            maxZoom={24}
                        />

                    case 'OUTPUT_DATA_TILE':
                        return <TileLayer key={layer.id}
                            url={`${Config.DATA_HOST}/tilemo/${layer.dsId}/{z}/{x}/{y}.png?bands=${layer.style.bands.join(",")}&vmin=${layer.style.min}&vmax=${layer.style.max}`}
                            maxZoom={24}
                        />
                    case 'PREVIEW_DATA_TILE':
                        return <TileLayer key={layer.id}
                            url={`${Config.DATA_HOST}/tilepro/${layer.dsId.replace("preview_", "")}/{z}/{x}/{y}.png?bands=${layer.style.bands.join(",")}&vmin=${layer.style.min}&vmax=${layer.style.max}`}
                            maxZoom={24}
                        />
                }
                return '';
            })
        }
    </div>
}


function ClickEvent(props) {
    const dispatch = useDispatch();
    const map = useMapEvent('click', (e) => {
        console.log(e.latlng)
    })
    return null
}

const Map = (props) => {
    const dispatch = useDispatch()
    const [markerPos, setMarkerPos] = useState(null)
    return (
        <MapContainer maxZoom={24} style={{ height: 'calc(100vh - 120px)', width: '100%' }} center={props.map.center} zoom={props.map.zoom}>
            {/*<ChangeMapZoom zoom={props.map.zoom} />*/}

            {/*<LayerHandler layers={props.map.layers} />*/}

            <MapViewChangeEvent />
            <ClickEvent timeIndexes={props.map.timeIndexes} tIndex={props.map.tIndex} setMarkerPos={setMarkerPos} />

            {/* <ChangeMapView
                center={props.map.mapView.center}
                zoom={props.map.mapView.zoom}
                changeMapView={props.map.changeMapView}
            /> */}
            <ChangeMapExtent
                extent={props.map.mapView.extent}
                changeMapView={props.map.changeMapView}
            />
            <MapLayers map={props.map} />
            {
                props.map.searchLayer ? (
                    <GeoJSON data={props.map.searchLayer.data} />
                ) : ''
            }

            {markerPos ? (<Marker position={markerPos}>
                {/* <Popup>
                    
                </Popup> */}
            </Marker>) : ''}
        </MapContainer>
    );
}

export default connect(mapStateToProps)(Map);