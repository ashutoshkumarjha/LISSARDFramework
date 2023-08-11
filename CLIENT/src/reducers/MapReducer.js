import * as AppConfig from '../utils/AppConfig'

const initialState = {
    // center: [-36.902306, 174.696037],
    center: [30.232603, 78.767992],//[29.1653,79.6124],
    zoom: 8,
    layers: AppConfig.layers,
    mapView: {
        center: [30.232603, 78.767992],
        zoom: 8,
        extent: [[40.712, -74.227],
        [40.774, -74.125]]
    },
    changeMapView: false,
    searchLayer: null,
    timeIndexes: null,
    dataVizMode: 'rgb',
    bands: [4, 3, 2],
    tIndex: null,
    vizMaxValue: 0.25,
    chartData: null,
    queryResults: []
};

const MapReducer = (state = initialState, action) => {
    let layers = state.layers;
    switch (action.type) {
        case "CHANGE_ZOOM":
            return {
                ...state,
                zoom: action.payload
            };
        case "CHANGE_MAP_VIEW":
            return {
                ...state,
                zoom: action.payload.zoom,
                center: action.payload.center,
                mapView: {
                    zoom: action.payload.zoom,
                    center: action.payload.center,
                    extent: state.mapView.extent
                },
                changeMapView: true
            };
        case "CHANGE_MAP_EXTENT":
            return {
                ...state,
                zoom: action.payload.zoom,
                center: action.payload.center,
                mapView: {
                    zoom: state.mapView.zoom,
                    center: state.mapView.center,
                    extent: action.payload.extent
                },
                changeMapView: true
            };
        case "MAP_VIEW_WAS_SET":
            return {
                ...state,
                zoom: action.payload.zoom,
                center: action.payload.center,
                mapView: {
                    zoom: action.payload.zoom,
                    center: action.payload.center,
                    extent: action.payload.extent
                },
                changeMapView: false
            };
        case "UPDATE_CHART_DATA":
            return {
                ...state,
                chartData: action.payload
            }
        case "UPDATE_RGB_BANDS":
            return {
                ...state,
                bands: [...action.payload.bands],
                vizMaxValue: action.payload.vizMaxValue
            }
        case "TOGGLE_LAYER_STATE":
            layers[action.payload.layerId].active = action.payload.active;
            return {
                ...state,
                layers: layers
            }
        case "CHANGE_LAYER_STYLE":
            layers[action.payload.layerId].style = action.payload.style;
            console.log(layers[action.payload.layerId].style)
            return {
                ...state,
                layers: layers
            }
        case "SET_TIME_INDEXEX":
            return {
                ...state,
                timeIndexes: action.payload
            }
        case "UPDATE_TINDEX":
            return {
                ...state,
                tIndex: action.payload
            }
        case "ADD_LAYER":
            layers[action.payload.id] = action.payload;
            return {
                ...state,
                layers: layers
            }
        case "REMOVE_LAYER":
            if (layers[action.payload])
                delete layers[action.payload]
            return {
                ...state,
                layers: layers
            }
        case "ADD_SEARCH_LAYER":
            if (Boolean(state.searchLayer) && Boolean(layers[state.searchLayer])) {
                delete layers[state.searchLayer];
            }
            return {
                ...state,
                searchLayer: action.payload,
                layers: { ...layers }
            }
        case "SET_QUERY_RESULTS":
            return {
                ...state,
                queryResults: action.payload
            }
        default:
            return {
                ...state
            };
    }
};

export default MapReducer;