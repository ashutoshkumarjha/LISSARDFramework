import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import DatePicker from 'react-datepicker';
import { Button, Slider, Tab, Tabs, Typography } from '@mui/material';
import { useDispatch } from 'react-redux';
import { addLayer, setQueryResults, setTimeIndexes, toggleAddAoiDialog, toggleAddLayerDialog, toggleQueryResultsDialog, toggleTasksDialog, updateRGBBands } from '../actions';
import DataService from '../services.js/Data';
import Config from '../config.js';

const TasksList = (props) => {

    const dispatch = useDispatch()

    const [tasks, setTasks] = React.useState([])

    const getTasks = () => {
        fetch(`${Config.DATA_HOST}/process/getAll`)
            .then(r => r.json())
            .then(r => {
                console.log(r)
                setTasks(r.data.map(d => {
                    return {
                        name: d.pname,
                        id: d.pid,
                        status: d.status
                    }
                }))
            })
            .catch(er => console.log(er))
    }

    React.useEffect(() => {
        getTasks()
    }, [])

    return <>
        <Typography variant="h6" gutterBottom component="div">
            Submitted Processes
        </Typography>
        <div style={{ textAlign: 'right' }}>
            <Button onClick={() => {
                getTasks()
            }}>Reload</Button>
        </div>
        <br />
        <Box sx={{ width: '100%', height: 500, overflowY: 'auto', border: '1px solid #333' }}>
            {
                tasks.map((task, tindx) => {
                    return <div style={{ padding: 12, margin: 6, border: '1px solid #888', height: 60 }}>
                        <div style={{ display: 'inline' }}>{tindx + 1}.{task.name} ({task.id})</div>
                        {task.status === 'COMPLETED' ? <div style={{ display: 'inline', float: 'right' }}>
                            <Button onClick={() => {
                                console.log(task);
                                let lId = (Math.random() + 1).toString(36).substring(6);
                                let layer = {
                                    type: 'OUTPUT_DATA_TILE',
                                    group: 'RASTER_DATA',
                                    id: lId,
                                    active: true,
                                    // tIndex: firstResult.tIndex,
                                    // tIndexes: props.map.queryResults.map(qr => qr.tIndex),
                                    // aoiCode: firstResult['aoiCode'],
                                    dsId: "output_" + task['id'],
                                    // noOfBands: firstResult['dsData']['no_of_bands'],
                                    name: "Output " + task['id'], // + ": " + firstResult.dsName,//'Layer: ' + firstResult.dsName + " #" + lId,
                                    sortOrder: 0,
                                    showLegend: false,
                                    showInLayerList: true,
                                    style: {
                                        min: 0,
                                        max: 1,
                                        bands: [4, 3, 2],
                                        type: "rgb"
                                    }
                                }
                                dispatch(addLayer(layer));
                                //https://test2.gishorizon.com/tilemo/output_UZFMUJOCKEJMTGML/12/2936/1686.png
                            }} >View</Button>
                            <Button onClick={() => {
                                var url = `${Config.DATA_HOST}/process/download?pid=${task.id}`;
                                window.open(url, '_blank');
                            }} >Download</Button>
                        </div> : <div style={{ display: 'inline', float: 'right' }}>{task.status}</div>}
                    </div>
                })
            }
        </Box>
        <br />
        <br />
        {/* <Button variant="contained" onClick={() => {
            dispatch(toggleTasksDialog(false))
        }}>Close</Button> */}
    </>
}

export default TasksList;