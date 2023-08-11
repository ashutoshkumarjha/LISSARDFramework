import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import DatePicker from 'react-datepicker';
import { Button, Slider, Typography } from '@mui/material';
import { connect, useDispatch } from 'react-redux';
import { addLayer, setQueryResults, setTimeIndexes, toggleAddLayerDialog, toggleQueryResultsDialog, updateRGBBands } from '../actions';
import Config from '../config.js';
import AppModal from './AppModal';
import DataService from '../services.js/Data';

const mapStateToProps = (state) => {
    return {
        map: state.MapReducer,
        dialog: state.DialogReducer
    }
}

const QueryPanel = (props) => {

    const dispatch = useDispatch()

    const [datasets, setDatasets] = React.useState([])


    const [sensor, setSensor] = React.useState("LISS3")
    // const [fromDate, setFromDate] = React.useState(new Date("1991-01-01"))
    // const [toDate, setToDate] = React.useState(new Date("1991-01-02"))
    const [fromDate, setFromDate] = React.useState(new Date("2017-01-01"))
    const [toDate, setToDate] = React.useState(new Date("2019-12-31"))
    const [aoi, setAoi] = React.useState('aoi_uk_1')

    const [redBand, setRedBand] = React.useState(4)
    const [greenBand, setGreenBand] = React.useState(3)
    const [blueBand, setBlueBand] = React.useState(2)
    const [vizMaxValue, setVizMaxValue] = React.useState(15000)

    const [timeValues, setTimeValues] = React.useState(null)

    React.useEffect(() => {
        // dispatch(updateRGBBands([redBand, greenBand, blueBand]))
    }, [redBand, greenBand, blueBand, vizMaxValue])

    const updateViz = () => {
        dispatch(updateRGBBands({
            bands: [redBand, greenBand, blueBand],
            vizMaxValue: vizMaxValue
        }))
    }

    const getDatasets = () => {
        fetch(`${Config.DATA_HOST}/getDatasets`)
            .then(r => r.json())
            .then(r => {
                setDatasets(r.data
                    // .filter(e => e.is_querable)
                    .map(d => {
                        return {
                            name: d.ds_name,
                            bands: JSON.parse(d.band_meta),
                            style: JSON.parse(d.def_color_scheme),
                            id: d.dataset_id,
                            description: d.ds_description,
                            vmin: d.vmin,
                            vmax: d.vmax,
                            noOfBands: d.no_of_bands
                        }
                    }))
            })
            .catch(er => console.log(er))
    }

    React.useEffect(() => {
        getDatasets()
    }, [])

    const queryDataset = async () => {
        let aoiCode = aoi;
        if (aoi === 'current_extent') {
            console.log(props.map.mapView.extent);
            let gj = {
                "coordinates": [
                    [
                        [
                            props.map.mapView.extent.getEast(),
                            props.map.mapView.extent.getSouth()
                        ],
                        [
                            props.map.mapView.extent.getEast(),
                            props.map.mapView.extent.getNorth()
                        ],
                        [
                            props.map.mapView.extent.getWest(),
                            props.map.mapView.extent.getNorth()
                        ],
                        [
                            props.map.mapView.extent.getWest(),
                            props.map.mapView.extent.getSouth()
                        ],
                        [
                            props.map.mapView.extent.getEast(),
                            props.map.mapView.extent.getSouth()
                        ]
                    ]
                ],
                "type": "Polygon"
            }
            let aoiData = await DataService.addAoi(JSON.stringify(gj), "Temp")
            aoiCode = aoiData.data;
        }
        fetch(`${Config.DATA_HOST}/getTimeIndexes?sensorName=${sensor}&fromTs=${fromDate.getTime()}&toTs=${toDate.getTime()}&aoi_code=${aoiCode}`)
            .then(r => r.json())
            .then(r => {
                if (r.data.length > 0) {
                    dispatch(toggleAddLayerDialog(false))
                    dispatch(setQueryResults(r.data))
                    dispatch(toggleQueryResultsDialog(true))
                } else {
                    alert("No result")
                }
            })
            .catch(e => {
                console.log(e)
            })
    }

    const aoiLayers = Object.keys(props.map.layers).filter(lk => props.map.layers[lk].group === "AOI").map(lk => props.map.layers[lk])
    return <AppModal btnText={"Add Layer"} flag={props.dialog.showAddLayerDialog} setFlag={(flag) => {
        dispatch(toggleAddLayerDialog(flag))
    }} content=<div>
        <Typography variant="h6" gutterBottom component="div">
            Query Datasets
        </Typography>
        <FormControl fullWidth>
            <InputLabel id="sensor-select">Sensor</InputLabel>
            <Select
                labelId="sensor-select"
                value={sensor}
                label="Sensor"
                onChange={(e) => { setSensor(e.target.value) }}
            >
                {
                    datasets.map(ds => {
                        return <MenuItem key={ds.name} value={ds.name}>{`${ds.name} - ${ds.description}`}</MenuItem>
                    })
                }
            </Select>
        </FormControl>
        <br /><br />
        <FormControl fullWidth>
            <InputLabel id="aoi-select">AOI</InputLabel>
            <Select
                labelId="aoi-select"
                value={aoi}
                label="AOI"
                onChange={(e) => { setAoi(e.target.value) }}
            >
                {
                    aoiLayers.map(aoiLayer => {
                        return <MenuItem value={aoiLayer.aoiCode}>{aoiLayer.name}</MenuItem>
                    })
                }
                <MenuItem value={"current_extent"}>Current extent</MenuItem>

            </Select>
        </FormControl>
        <br /><br />
        <Typography variant="body2">From date</Typography>
        <DatePicker
            style={{
                "padding": 8
            }}
            selected={fromDate}
            onChange={(date) => setFromDate(date)}
        />
        <br />
        <Typography variant="body2">To date</Typography>
        <DatePicker
            style={{
                "padding": 8
            }}
            selected={toDate}
            onChange={(date) => setToDate(date)}
        />
        <br />

        <br />
        <Button variant="contained" onClick={queryDataset}>Submit</Button>
        <br />
    </div>
    />
}

export default connect(mapStateToProps)(QueryPanel);