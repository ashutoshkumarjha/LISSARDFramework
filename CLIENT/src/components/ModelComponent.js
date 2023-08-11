const AddedLayers = [
    {
        layerId: "Layer_51637",
        datasetId: 'landsat_8',
        dataTimes: [1609565100000],
        temporalIndexes: [978413100],
        isMultitemporal: false,
        datasetMeta: {
            id: 'landsat_8',
            dataType: 'int16',
            noOfBands: 7,
            name: "Landsat 8",
            description: "OLI Landsat 8",
            defaultColorScheme: {
                type: "stretched",
                colorRamp: [
                    "#000000",
                    "#ffffff"
                ]
            },
            bandMeta: [
                {
                    name: "Band 1",
                    description: "Coastal Aerosol",
                    min: 2,
                    max: 1000
                },
                {
                    name: "Band 2",
                    description: "Blue",
                    min: 100,
                    max: 1200
                },
                {
                    name: "Band 3",
                    description: "Green",
                    min: 300,
                    max: 1600
                },
                {
                    name: "Band 4",
                    description: "Red",
                    min: 0,
                    max: 2600
                },
                {
                    name: "Band 5",
                    description: "NIR",
                    min: 100,
                    max: 4500
                },
                {
                    name: "Band 6",
                    description: "SWIR1",
                    min: -200,
                    max: 4100
                },
                {
                    name: "Band 7",
                    description: "SWIR2",
                    min: -200,
                    max: 4200
                }
            ]
        },
        aoi: { "type": "Polygon", "coordinates": [ [ [ 89.332714052406857, 26.263876189808741 ], [ 89.343291455718855, 26.263860163440086 ], [ 89.3432754293502, 26.251968597898411 ], [ 89.332698026038202, 26.252016677004377 ], [ 89.332714052406857, 26.263876189808741 ] ] ] }
    }
]

const InputRasterLayer = (props) => {
    return <>
        <select>
            {
                AddedLayers.map(layer=>{
                    return <option key={layer.layerId} value={layer.layerId}>{`${layer.layerId} - ${layer.datasetMeta.name}`}</option>
                })
            }
        </select>

    </>
}

const InputRasterBand = (props) => {
    return <>
        <select>
            {
                AddedLayers.map(layer=>{
                    return <option key={layer.layerId} value={layer.layerId}>{`${layer.layerId} - ${layer.datasetMeta.name}`}</option>
                })
            }
        </select>
        <br/>
        <select>
            {
                AddedLayers[0].datasetMeta.bandMeta.map(band=>{
                    return <option key={band.name} value={band.name}>{`${band.name}`}</option>
                })
            }
        </select>

    </>
}

const OperationLocalAverage = (props) => {
    return <>
        <p>Pixel Avg.</p>
        {
                AddedLayers[0].datasetMeta.bandMeta.map(band=>{
                    return <>
                        <input type="checkbox" key={band.name} /> {band.name} <br/>
                    </>
                })
            }
    </>
}

const OutputRasterLayer = (props) => {
    return <>
        <p>Output</p>
        <input type="text" />
    </>
}

const ModelComponent = (props) => {
    // console.log(props)
    let Comp = <>None</>;
    switch(props.type){
        case 'in_raster_layer':
            Comp = <InputRasterLayer />;
            break;
        case 'in_raster_band':
            Comp = <InputRasterBand />;
            break;
        case 'op_local_avg':
            Comp = <OperationLocalAverage />;
            break;
        case 'op_raster_layer':
            Comp = <OutputRasterLayer />
            break;
    }
    return Comp
}

export default ModelComponent;