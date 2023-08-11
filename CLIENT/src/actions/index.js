export const toggleLayerState = (layerId, active) => {
    return {
        type: 'TOGGLE_LAYER_STATE',
        payload: { layerId, active }
    }
};
export const changeLayerStyle = (layerId, style) => {
    return {
        type: 'CHANGE_LAYER_STYLE',
        payload: { layerId, style }
    }
};
export const changeMapZoom = (zoom) => {
    return {
        type: 'CHANGE_ZOOM',
        payload: zoom
    }
}
export const changeMapView = (center, zoom) => {
    return {
        type: 'CHANGE_MAP_VIEW',
        payload: { center, zoom }
    }
}
export const changeMapExtent = (extent) => {
    return {
        type: 'CHANGE_MAP_EXTENT',
        payload: { extent }
    }
}
export const mapViewWasSet = (center, zoom, extent) => {
    return {
        type: 'MAP_VIEW_WAS_SET',
        payload: { center, zoom, extent }
    }
}
export const addLayer = (layer) => {
    return {
        type: 'ADD_LAYER',
        payload: layer
    }
};
export const removeLayer = (layerId) => {
    return {
        type: 'REMOVE_LAYER',
        payload: layerId
    }
};
export const addSearchLayer = (layer) => {
    return {
        type: 'ADD_SEARCH_LAYER',
        payload: layer
    }
};

export const setTimeIndexes = (data) => {
    return {
        type: 'SET_TIME_INDEXEX',
        payload: data
    }
};

export const updateTimeIndex = (data) => {
    return {
        type: "UPDATE_TINDEX",
        payload: data
    }
}

export const updateRGBBands = (data) => {
    return {
        type: "UPDATE_RGB_BANDS",
        payload: data
    }
}

export const updateChartData = (data) => {
    return {
        type: "UPDATE_CHART_DATA",
        payload: data
    }
}
export const toggleAddLayerDialog = (flag) => {
    return {
        type: 'TOGGLE_ADD_LAYER',
        payload: flag
    }
};
export const toggleAddAoiDialog = (flag) => {
    return {
        type: 'TOGGLE_ADD_AOI',
        payload: flag
    }
};
export const toggleModelBuilderDialog = (flag) => {
    return {
        type: 'TOGGLE_MODEL_BUILDER',
        payload: flag
    }
};
export const toggleQueryResultsDialog = (flag) => {
    return {
        type: 'TOGGLE_QUERY_RESULTS_DIALOG',
        payload: flag
    }
};
export const setQueryResults = (data) => {
    return {
        type: 'SET_QUERY_RESULTS',
        payload: data
    }
};
export const toggleTasksDialog = (flag) => {
    return {
        type: 'TOGGLE_TASKS_DIALOG',
        payload: flag
    }
};